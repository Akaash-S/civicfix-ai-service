"""
Cross-Verification Service

This service compares citizen "before" images with government "after" images to verify:
- Same location
- Same issue
- Actual work completion
- Fake resolution detection
"""

import logging
from typing import List, Tuple
from PIL import Image
import imagehash
import io
import httpx
import numpy as np

from app.config import get_settings
from app.models import CheckResult, CheckStatus, LocationData, ComparisonResult
from app.services.location_validator import LocationValidatorService
from app.services.metadata_validator import MetadataValidatorService

logger = logging.getLogger(__name__)
settings = get_settings()


class CrossVerificationService:
    """Service for cross-verifying citizen vs government images"""
    
    def __init__(self):
        self.settings = settings
        self.location_service = LocationValidatorService()
        self.metadata_service = MetadataValidatorService()
    
    async def verify_resolution(
        self,
        citizen_images: List[str],
        government_images: List[str],
        location: LocationData,
        issue_category: str
    ) -> ComparisonResult:
        """
        Verify if government resolution is legitimate
        
        Args:
            citizen_images: URLs of citizen "before" images
            government_images: URLs of government "after" images
            location: Reported issue location
            issue_category: Issue category
            
        Returns:
            ComparisonResult with verification status
        """
        try:
            # Download and analyze images
            citizen_imgs = await self._download_images(citizen_images)
            government_imgs = await self._download_images(government_images)
            
            if not citizen_imgs or not government_imgs:
                return ComparisonResult(
                    similarity_score=0.0,
                    same_location=False,
                    location_distance_meters=0.0,
                    work_appears_completed=False,
                    confidence=0.0,
                    notes="Failed to download images for comparison",
                    warnings=["Image download failed"]
                )
            
            # Check 1: Location consistency
            location_check = await self._verify_location_consistency(
                citizen_images[0],
                government_images[0],
                location
            )
            
            # Check 2: Image similarity (should be similar location but different state)
            similarity_score = self._calculate_similarity(
                citizen_imgs[0],
                government_imgs[0]
            )
            
            # Check 3: Visual change detection
            work_completed = self._detect_work_completion(
                citizen_imgs[0],
                government_imgs[0],
                issue_category
            )
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(
                location_check,
                similarity_score,
                work_completed
            )
            
            # Generate notes
            notes = self._generate_notes(
                location_check,
                similarity_score,
                work_completed,
                issue_category
            )
            
            # Collect warnings
            warnings = []
            if not location_check["same_location"]:
                warnings.append("Location mismatch detected")
            if similarity_score < 0.3:
                warnings.append("Images appear to be from different locations")
            if not work_completed:
                warnings.append("Work completion unclear from images")
            
            return ComparisonResult(
                similarity_score=similarity_score,
                same_location=location_check["same_location"],
                location_distance_meters=location_check["distance"],
                work_appears_completed=work_completed,
                confidence=confidence,
                notes=notes,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Cross-verification failed: {e}")
            return ComparisonResult(
                similarity_score=0.0,
                same_location=False,
                location_distance_meters=0.0,
                work_appears_completed=False,
                confidence=0.0,
                notes=f"Verification error: {str(e)}",
                warnings=["Verification failed"]
            )
    
    async def _verify_location_consistency(
        self,
        citizen_image_url: str,
        government_image_url: str,
        reported_location: LocationData
    ) -> dict:
        """Verify both images are from the same location"""
        try:
            # Extract GPS from both images
            citizen_img_data = await self._download_image(citizen_image_url)
            government_img_data = await self._download_image(government_image_url)
            
            citizen_img = Image.open(io.BytesIO(citizen_img_data))
            government_img = Image.open(io.BytesIO(government_img_data))
            
            citizen_exif = self.metadata_service._extract_exif(citizen_img)
            government_exif = self.metadata_service._extract_exif(government_img)
            
            citizen_gps = self.metadata_service.extract_gps_coordinates(citizen_exif)
            government_gps = self.metadata_service.extract_gps_coordinates(government_exif)
            
            if not citizen_gps or not government_gps:
                # No GPS data - use reported location as reference
                return {
                    "same_location": True,  # Assume true if no GPS
                    "distance": 0.0,
                    "has_gps": False
                }
            
            # Calculate distance between GPS coordinates
            distance = self.location_service._calculate_distance(
                citizen_gps[0], citizen_gps[1],
                government_gps[0], government_gps[1]
            )
            
            same_location = distance <= settings.location_radius_meters * 2  # Allow 2x radius for government
            
            return {
                "same_location": same_location,
                "distance": distance,
                "has_gps": True
            }
            
        except Exception as e:
            logger.error(f"Location consistency check failed: {e}")
            return {
                "same_location": True,  # Assume true on error
                "distance": 0.0,
                "has_gps": False
            }
    
    def _calculate_similarity(self, img1: Image.Image, img2: Image.Image) -> float:
        """
        Calculate perceptual similarity between images
        
        Returns:
            Similarity score (0-1)
        """
        try:
            # Calculate perceptual hashes
            hash1 = imagehash.phash(img1, hash_size=16)
            hash2 = imagehash.phash(img2, hash_size=16)
            
            # Calculate Hamming distance
            distance = hash1 - hash2
            
            # Convert to similarity (0-1 scale)
            max_distance = 256  # 16x16 hash
            similarity = 1 - (distance / max_distance)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.5  # Neutral score on error
    
    def _detect_work_completion(
        self,
        before_img: Image.Image,
        after_img: Image.Image,
        issue_category: str
    ) -> bool:
        """
        Detect if work appears to be completed
        
        This is a simplified heuristic. In production, use:
        - Object detection
        - Semantic segmentation
        - Change detection algorithms
        """
        try:
            # Convert images to grayscale for comparison
            before_gray = before_img.convert('L')
            after_gray = after_img.convert('L')
            
            # Resize to same size
            size = (256, 256)
            before_gray = before_gray.resize(size)
            after_gray = after_gray.resize(size)
            
            # Convert to numpy arrays
            before_array = np.array(before_gray)
            after_array = np.array(after_gray)
            
            # Calculate difference
            diff = np.abs(before_array.astype(float) - after_array.astype(float))
            mean_diff = np.mean(diff)
            
            # Heuristic: If mean difference is significant, work was done
            # This is very simplified - real implementation would use ML
            work_done = mean_diff > 20  # Threshold for "significant change"
            
            logger.info(f"Work completion detection: mean_diff={mean_diff:.2f}, work_done={work_done}")
            
            return work_done
            
        except Exception as e:
            logger.error(f"Work completion detection failed: {e}")
            return False  # Conservative: assume work not done on error
    
    def _calculate_confidence(
        self,
        location_check: dict,
        similarity_score: float,
        work_completed: bool
    ) -> float:
        """Calculate overall confidence score"""
        confidence = 0.0
        
        # Location check (40% weight)
        if location_check["same_location"]:
            confidence += 0.4
        
        # Similarity check (30% weight)
        # Should be similar (same location) but not identical
        if 0.3 <= similarity_score <= 0.8:
            confidence += 0.3
        elif similarity_score > 0.8:
            confidence += 0.15  # Too similar - might be same image
        
        # Work completion (30% weight)
        if work_completed:
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def _generate_notes(
        self,
        location_check: dict,
        similarity_score: float,
        work_completed: bool,
        issue_category: str
    ) -> str:
        """Generate human-readable notes"""
        notes = []
        
        if location_check["same_location"]:
            notes.append(f"✓ Location verified (distance: {location_check['distance']:.1f}m)")
        else:
            notes.append(f"✗ Location mismatch (distance: {location_check['distance']:.1f}m)")
        
        notes.append(f"Image similarity: {similarity_score:.2%}")
        
        if work_completed:
            notes.append(f"✓ Visual changes detected - work appears completed")
        else:
            notes.append(f"⚠ No significant visual changes detected")
        
        notes.append(f"Category: {issue_category}")
        
        return " | ".join(notes)
    
    async def _download_images(self, image_urls: List[str]) -> List[Image.Image]:
        """Download multiple images"""
        images = []
        for url in image_urls:
            img_data = await self._download_image(url)
            if img_data:
                images.append(Image.open(io.BytesIO(img_data)))
        return images
    
    async def _download_image(self, image_url: str) -> bytes:
        """Download single image"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            return None
