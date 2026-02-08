"""
Duplicate Image Detection Service

This service detects:
- Exact duplicate images
- Near-duplicate images (perceptual hashing)
- Previously submitted images
- Reused images across issues
"""

import logging
from typing import Tuple, List, Optional
from PIL import Image
import imagehash
import io
import httpx

from app.config import get_settings
from app.models import CheckResult, CheckStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class DuplicateDetectionService:
    """Service for detecting duplicate images"""
    
    def __init__(self):
        self.settings = settings
        # In-memory cache of image hashes (in production, use Redis or database)
        self.hash_cache = {}
    
    async def detect_duplicate(
        self,
        image_url: str,
        issue_id: Optional[int] = None
    ) -> CheckResult:
        """
        Detect if image is a duplicate
        
        Args:
            image_url: URL of the image to check
            issue_id: Current issue ID (to exclude from duplicate check)
            
        Returns:
            CheckResult with duplicate detection status
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
            
            # Calculate perceptual hash
            phash = self._calculate_phash(image)
            
            # Check for duplicates
            duplicate_found, similarity, duplicate_issue_id = self._check_duplicates(
                phash,
                issue_id
            )
            
            if duplicate_found:
                return CheckResult(
                    status=CheckStatus.FAILED,
                    confidence=similarity,
                    details=f"Duplicate image detected (similarity: {similarity:.2%}). "
                           f"Previously used in issue #{duplicate_issue_id}",
                    metadata={
                        "duplicate_issue_id": duplicate_issue_id,
                        "similarity_score": similarity,
                        "hash": str(phash)
                    }
                )
            else:
                # Store hash for future checks
                self._store_hash(phash, issue_id)
                
                return CheckResult(
                    status=CheckStatus.PASSED,
                    confidence=0.95,
                    details="No duplicate detected",
                    metadata={"hash": str(phash)}
                )
                
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
            return CheckResult(
                status=CheckStatus.FAILED,
                confidence=0.0,
                details=f"Detection error: {str(e)}"
            )
    
    def _calculate_phash(self, image: Image.Image) -> imagehash.ImageHash:
        """
        Calculate perceptual hash of image
        
        Uses pHash algorithm which is robust to:
        - Resizing
        - Compression
        - Minor edits
        - Color adjustments
        """
        return imagehash.phash(image, hash_size=16)
    
    def _check_duplicates(
        self,
        phash: imagehash.ImageHash,
        current_issue_id: Optional[int]
    ) -> Tuple[bool, float, Optional[int]]:
        """
        Check if hash matches any stored hashes
        
        Returns:
            (is_duplicate, similarity_score, duplicate_issue_id)
        """
        for stored_hash_str, stored_issue_id in self.hash_cache.items():
            # Skip if same issue
            if current_issue_id and stored_issue_id == current_issue_id:
                continue
            
            stored_hash = imagehash.hex_to_hash(stored_hash_str)
            
            # Calculate Hamming distance
            distance = phash - stored_hash
            
            # Convert distance to similarity (0-1 scale)
            # Hash size is 16, so max distance is 16*16 = 256
            max_distance = 256
            similarity = 1 - (distance / max_distance)
            
            # Check if similarity exceeds threshold
            if similarity >= settings.duplicate_threshold:
                return True, similarity, stored_issue_id
        
        return False, 0.0, None
    
    def _store_hash(self, phash: imagehash.ImageHash, issue_id: Optional[int]):
        """Store hash for future duplicate checks"""
        self.hash_cache[str(phash)] = issue_id
        
        # TODO: In production, store in Redis or database
        # Example:
        # redis_client.set(f"image_hash:{phash}", issue_id)
    
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
    
    async def batch_detect(
        self,
        image_urls: List[str],
        issue_id: Optional[int] = None
    ) -> List[CheckResult]:
        """
        Detect duplicates in batch
        
        Args:
            image_urls: List of image URLs
            issue_id: Current issue ID
            
        Returns:
            List of CheckResult objects
        """
        results = []
        for url in image_urls:
            result = await self.detect_duplicate(url, issue_id)
            results.append(result)
        return results
    
    def clear_cache(self):
        """Clear hash cache (for testing)"""
        self.hash_cache.clear()
    
    def get_cache_size(self) -> int:
        """Get number of hashes in cache"""
        return len(self.hash_cache)
