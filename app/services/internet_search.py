"""
Internet Image Search Service

This service performs reverse image search to detect:
- Images reused from the internet
- Stock photos
- Previously published images
- Fake evidence
"""

import logging
from typing import Optional, List, Dict, Any
from PIL import Image
import io
import httpx
import hashlib

from app.config import get_settings
from app.models import CheckResult, CheckStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class InternetSearchService:
    """Service for reverse image search"""
    
    def __init__(self):
        self.settings = settings
        self.search_enabled = settings.reverse_image_search_enabled
    
    async def search_image(self, image_url: str) -> CheckResult:
        """
        Perform reverse image search
        
        Args:
            image_url: URL of the image to search
            
        Returns:
            CheckResult with search results
        """
        if not self.search_enabled:
            return CheckResult(
                status=CheckStatus.SKIPPED,
                confidence=0.0,
                details="Internet search disabled"
            )
        
        try:
            # Download image
            image_data = await self._download_image(image_url)
            if not image_data:
                return CheckResult(
                    status=CheckStatus.FAILED,
                    confidence=0.0,
                    details="Failed to download image"
                )
            
            # Perform search
            search_results = await self._perform_search(image_data)
            
            if not search_results:
                # No matches found - good sign
                return CheckResult(
                    status=CheckStatus.PASSED,
                    confidence=0.9,
                    details="No matches found on the internet. Image appears original.",
                    metadata={"matches_found": 0}
                )
            
            # Analyze results
            return self._analyze_results(search_results)
            
        except Exception as e:
            logger.error(f"Internet search failed: {e}")
            return CheckResult(
                status=CheckStatus.FAILED,
                confidence=0.0,
                details=f"Search error: {str(e)}"
            )
    
    async def _perform_search(self, image_data: bytes) -> Optional[List[Dict[str, Any]]]:
        """
        Perform actual reverse image search
        
        TODO: Integrate with reverse image search API
        - Google Vision API
        - TinEye API
        - Bing Visual Search
        """
        if settings.enable_mock_ai:
            # Mock search - return no results
            return None
        
        try:
            # TODO: Implement actual API integration
            # Example with Google Vision API:
            # from google.cloud import vision
            # client = vision.ImageAnnotatorClient()
            # image = vision.Image(content=image_data)
            # response = client.web_detection(image=image)
            # return response.web_detection.pages_with_matching_images
            
            return None
            
        except Exception as e:
            logger.error(f"Search API call failed: {e}")
            return None
    
    def _analyze_results(self, results: List[Dict[str, Any]]) -> CheckResult:
        """Analyze search results"""
        num_matches = len(results)
        
        if num_matches == 0:
            return CheckResult(
                status=CheckStatus.PASSED,
                confidence=0.9,
                details="No matches found",
                metadata={"matches_found": 0}
            )
        
        # Check if matches are from stock photo sites
        stock_sites = ['shutterstock', 'getty', 'istockphoto', 'unsplash', 'pexels']
        stock_matches = [
            r for r in results
            if any(site in r.get('url', '').lower() for site in stock_sites)
        ]
        
        if stock_matches:
            return CheckResult(
                status=CheckStatus.FAILED,
                confidence=0.2,
                details=f"Image found on stock photo sites ({len(stock_matches)} matches). "
                       f"This appears to be a reused stock image.",
                metadata={
                    "matches_found": num_matches,
                    "stock_matches": len(stock_matches),
                    "sources": [r.get('url') for r in stock_matches[:5]]
                }
            )
        
        # Check if matches are from news/social media
        if num_matches > 5:
            return CheckResult(
                status=CheckStatus.WARNING,
                confidence=0.5,
                details=f"Image found in {num_matches} locations on the internet. "
                       f"May be reused from another source.",
                metadata={
                    "matches_found": num_matches,
                    "sources": [r.get('url') for r in results[:5]]
                }
            )
        
        # Few matches - might be legitimate
        return CheckResult(
            status=CheckStatus.WARNING,
            confidence=0.7,
            details=f"Image found in {num_matches} locations. Verify authenticity.",
            metadata={
                "matches_found": num_matches,
                "sources": [r.get('url') for r in results]
            }
        )
    
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
    
    def _calculate_image_hash(self, image_data: bytes) -> str:
        """Calculate hash of image for caching"""
        return hashlib.sha256(image_data).hexdigest()
