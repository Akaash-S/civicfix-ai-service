"""
Metadata Validation Service

This service validates:
- EXIF data presence and consistency
- GPS coordinates in EXIF
- Timestamp validation
- Camera information
- Image manipulation detection via metadata
"""

import logging
from typing import Dict, Any, Optional, Tuple
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import httpx
from datetime import datetime

from app.config import get_settings
from app.models import CheckResult, CheckStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class MetadataValidatorService:
    """Service for validating image metadata"""
    
    def __init__(self):
        self.settings = settings
    
    async def validate_metadata(self, image_url: str) -> CheckResult:
        """
        Validate image metadata
        
        Args:
            image_url: URL of the image to validate
            
        Returns:
            CheckResult with validation status
        """
        try:
            # Download image
            image_data = await self._download_image(image_url)
            if not image_data:
                return CheckResult(
                    status=CheckStatus.FAILED,
                    confidence=0.0,
                    details="Failed to download image"
                )
            
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Extract EXIF data
            exif_data = self._extract_exif(image)
            
            # Validate metadata
            validation_result = self._validate_exif_data(exif_data)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Metadata validation failed: {e}")
            return CheckResult(
                status=CheckStatus.FAILED,
                confidence=0.0,
                details=f"Validation error: {str(e)}"
            )
    
    def _extract_exif(self, image: Image.Image) -> Dict[str, Any]:
        """Extract EXIF data from image"""
        exif_data = {}
        
        try:
            exif = image.getexif()
            
            if not exif:
                return exif_data
            
            # Extract standard EXIF tags
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                exif_data[tag_name] = value
            
            # Extract GPS data if present
            if 'GPSInfo' in exif_data:
                gps_data = {}
                for key in exif_data['GPSInfo'].keys():
                    tag_name = GPSTAGS.get(key, key)
                    gps_data[tag_name] = exif_data['GPSInfo'][key]
                exif_data['GPSInfo'] = gps_data
            
        except Exception as e:
            logger.warning(f"Failed to extract EXIF data: {e}")
        
        return exif_data
    
    def _validate_exif_data(self, exif_data: Dict[str, Any]) -> CheckResult:
        """Validate EXIF data for authenticity"""
        warnings = []
        confidence = 1.0
        has_issues = False
        
        # Check 1: EXIF data presence
        if not exif_data or len(exif_data) == 0:
            warnings.append("No EXIF data found (common in screenshots or edited images)")
            confidence = 0.6
            has_issues = True
        
        # Check 2: Camera information
        if 'Make' not in exif_data or 'Model' not in exif_data:
            warnings.append("Missing camera make/model information")
            confidence = min(confidence, 0.7)
        else:
            camera_info = f"{exif_data.get('Make', '')} {exif_data.get('Model', '')}"
            logger.info(f"Camera: {camera_info}")
        
        # Check 3: Timestamp validation
        if 'DateTime' in exif_data or 'DateTimeOriginal' in exif_data:
            timestamp_str = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
            try:
                # Parse timestamp
                timestamp = datetime.strptime(timestamp_str, '%Y:%m:%d %H:%M:%S')
                
                # Check if timestamp is in the future
                if timestamp > datetime.now():
                    warnings.append("Image timestamp is in the future")
                    confidence = min(confidence, 0.5)
                    has_issues = True
                
                # Check if timestamp is too old (>5 years)
                age_days = (datetime.now() - timestamp).days
                if age_days > 1825:  # 5 years
                    warnings.append(f"Image is very old ({age_days} days)")
                    confidence = min(confidence, 0.7)
                
            except Exception as e:
                warnings.append(f"Invalid timestamp format: {timestamp_str}")
                confidence = min(confidence, 0.7)
        else:
            warnings.append("No timestamp information found")
            confidence = min(confidence, 0.75)
        
        # Check 4: GPS data presence
        has_gps = 'GPSInfo' in exif_data and exif_data['GPSInfo']
        if not has_gps:
            warnings.append("No GPS data in EXIF (location cannot be verified from metadata)")
            confidence = min(confidence, 0.8)
        
        # Check 5: Software/editing detection
        if 'Software' in exif_data:
            software = exif_data['Software'].lower()
            editing_software = ['photoshop', 'gimp', 'lightroom', 'snapseed', 'vsco']
            if any(editor in software for editor in editing_software):
                warnings.append(f"Image edited with: {exif_data['Software']}")
                confidence = min(confidence, 0.6)
                has_issues = True
        
        # Determine status
        if has_issues or confidence < 0.7:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.PASSED
        
        details = "Metadata validation complete. " + "; ".join(warnings) if warnings else "Metadata appears valid"
        
        return CheckResult(
            status=status,
            confidence=confidence,
            details=details,
            metadata={
                "has_exif": bool(exif_data),
                "has_gps": has_gps,
                "has_camera_info": 'Make' in exif_data and 'Model' in exif_data,
                "has_timestamp": 'DateTime' in exif_data or 'DateTimeOriginal' in exif_data,
                "warnings_count": len(warnings)
            }
        )
    
    def extract_gps_coordinates(self, exif_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """
        Extract GPS coordinates from EXIF data
        
        Returns:
            (latitude, longitude) or None if not available
        """
        try:
            if 'GPSInfo' not in exif_data:
                return None
            
            gps_info = exif_data['GPSInfo']
            
            # Extract latitude
            if 'GPSLatitude' in gps_info and 'GPSLatitudeRef' in gps_info:
                lat = self._convert_to_degrees(gps_info['GPSLatitude'])
                if gps_info['GPSLatitudeRef'] == 'S':
                    lat = -lat
            else:
                return None
            
            # Extract longitude
            if 'GPSLongitude' in gps_info and 'GPSLongitudeRef' in gps_info:
                lon = self._convert_to_degrees(gps_info['GPSLongitude'])
                if gps_info['GPSLongitudeRef'] == 'W':
                    lon = -lon
            else:
                return None
            
            return (lat, lon)
            
        except Exception as e:
            logger.error(f"Failed to extract GPS coordinates: {e}")
            return None
    
    def _convert_to_degrees(self, value):
        """Convert GPS coordinates to degrees"""
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)
    
    async def _download_image(self, image_url: str) -> bytes:
        """Download image from URL"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            return None
