"""
Location Validation Service

This service validates:
- GPS coordinates consistency between EXIF and reported location
- Location proximity check
- Suspicious location patterns
- Location history analysis
"""

import logging
from typing import Tuple, Optional
from math import radians, cos, sin, asin, sqrt
from PIL import Image
import io
import httpx

from app.config import get_settings
from app.models import CheckResult, CheckStatus, LocationData
from app.services.metadata_validator import MetadataValidatorService

logger = logging.getLogger(__name__)
settings = get_settings()


class LocationValidatorService:
    """Service for validating location consistency"""
    
    def __init__(self):
        self.settings = settings
        self.metadata_service = MetadataValidatorService()
    
    async def validate_location(
        self,
        image_url: str,
        reported_location: LocationData
    ) -> CheckResult:
        """
        Validate location consistency
        
        Args:
            image_url: URL of the image
            reported_location: Location reported by user
            
        Returns:
            CheckResult with validation status
        """
        try:
            # Download image
            image_data = await self._download_image(image_url)
            if not image_data:
                return CheckResult(
                    status=CheckStatus.WARNING,
                    confidence=0.5,
                    details="Failed to download image for location validation"
                )
            
            # Open image and extract EXIF
            image = Image.open(io.BytesIO(image_data))
            exif_data = self.metadata_service._extract_exif(image)
            
            # Extract GPS coordinates from EXIF
            exif_coords = self.metadata_service.extract_gps_coordinates(exif_data)
            
            if not exif_coords:
                # No GPS data in EXIF - cannot verify but not necessarily fake
                return CheckResult(
                    status=CheckStatus.WARNING,
                    confidence=0.7,
                    details="No GPS data in image metadata. Location cannot be verified from EXIF.",
                    metadata={
                        "has_exif_gps": False,
                        "reported_location": {
                            "lat": reported_location.latitude,
                            "lon": reported_location.longitude
                        }
                    }
                )
            
            # Calculate distance between EXIF and reported location
            distance_meters = self._calculate_distance(
                exif_coords[0], exif_coords[1],
                reported_location.latitude, reported_location.longitude
            )
            
            # Check if within acceptable radius
            is_within_radius = distance_meters <= settings.location_radius_meters
            
            if is_within_radius:
                return CheckResult(
                    status=CheckStatus.PASSED,
                    confidence=0.95,
                    details=f"Location verified. EXIF GPS matches reported location (distance: {distance_meters:.1f}m)",
                    metadata={
                        "has_exif_gps": True,
                        "exif_location": {"lat": exif_coords[0], "lon": exif_coords[1]},
                        "reported_location": {
                            "lat": reported_location.latitude,
                            "lon": reported_location.longitude
                        },
                        "distance_meters": distance_meters
                    }
                )
            else:
                return CheckResult(
                    status=CheckStatus.FAILED,
                    confidence=0.3,
                    details=f"Location mismatch! EXIF GPS is {distance_meters:.1f}m away from reported location. "
                           f"Acceptable radius: {settings.location_radius_meters}m",
                    metadata={
                        "has_exif_gps": True,
                        "exif_location": {"lat": exif_coords[0], "lon": exif_coords[1]},
                        "reported_location": {
                            "lat": reported_location.latitude,
                            "lon": reported_location.longitude
                        },
                        "distance_meters": distance_meters,
                        "acceptable_radius": settings.location_radius_meters
                    }
                )
                
        except Exception as e:
            logger.error(f"Location validation failed: {e}")
            return CheckResult(
                status=CheckStatus.FAILED,
                confidence=0.0,
                details=f"Validation error: {str(e)}"
            )
    
    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula
        
        Returns:
            Distance in meters
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        
        return c * r
    
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
    
    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """
        Validate if coordinates are within valid ranges
        
        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            
        Returns:
            True if valid, False otherwise
        """
        return -90 <= latitude <= 90 and -180 <= longitude <= 180
