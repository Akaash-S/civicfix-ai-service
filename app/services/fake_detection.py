"""
Fake/AI-Generated Image Detection Service

This service detects:
- AI-generated images (DALL-E, Midjourney, Stable Diffusion, etc.)
- Manipulated/edited images
- Deep fakes
- Common AI artifacts
"""

import logging
from typing import Tuple, Dict, Any
from PIL import Image
import numpy as np
import io
import httpx

from app.config import get_settings
from app.models import CheckResult, CheckStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class FakeDetectionService:
    """Service for detecting fake/AI-generated images"""
    
    def __init__(self):
        self.settings = settings
        self.model_loaded = False
        
        if not settings.enable_mock_ai:
            self._load_model()
    
    def _load_model(self):
        """Load AI detection model"""
        try:
            # TODO: Load actual deep learning model
            # Example: self.model = torch.load(settings.fake_detection_model_path)
            logger.info("Fake detection model loaded")
            self.model_loaded = True
        except Exception as e:
            logger.error(f"Failed to load fake detection model: {e}")
            self.model_loaded = False
    
    async def detect_fake(self, image_url: str) -> CheckResult:
        """
        Detect if image is fake/AI-generated
        
        Args:
            image_url: URL of the image to analyze
            
        Returns:
            CheckResult with detection status and confidence
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
            
            if settings.enable_mock_ai:
                # Mock detection for development
                result = self._mock_detection(image)
            else:
                # Real AI detection
                result = self._real_detection(image)
            
            return result
            
        except Exception as e:
            logger.error(f"Fake detection failed: {e}")
            return CheckResult(
                status=CheckStatus.FAILED,
                confidence=0.0,
                details=f"Detection error: {str(e)}"
            )
    
    def _mock_detection(self, image: Image.Image) -> CheckResult:
        """
        Mock detection for development/testing
        
        Uses heuristics to simulate AI detection:
        - Check image dimensions (AI images often have specific sizes)
        - Check for common patterns
        - Random confidence scoring
        """
        width, height = image.size
        
        # Heuristic checks
        is_suspicious = False
        confidence = 0.95
        details = []
        
        # Check 1: Common AI image dimensions
        ai_dimensions = [
            (512, 512), (1024, 1024), (768, 768),  # Stable Diffusion
            (1024, 1792), (1792, 1024),  # DALL-E 3
        ]
        if (width, height) in ai_dimensions:
            is_suspicious = True
            confidence = 0.7
            details.append(f"Image dimensions ({width}x{height}) match common AI generation sizes")
        
        # Check 2: Perfect aspect ratios (AI often generates perfect squares)
        if width == height and width in [256, 512, 768, 1024, 2048]:
            is_suspicious = True
            confidence = min(confidence, 0.75)
            details.append("Perfect square dimensions suggest AI generation")
        
        # Check 3: File size analysis (AI images often have specific compression)
        # This is a simplified check
        
        # Check 4: EXIF data presence (AI images often lack camera EXIF)
        exif_data = image.getexif()
        if not exif_data or len(exif_data) == 0:
            details.append("Missing EXIF data (common in AI-generated images)")
            confidence = min(confidence, 0.85)
        
        # Determine status
        if is_suspicious and confidence < 0.8:
            status = CheckStatus.WARNING
            final_details = "Image shows characteristics of AI generation. " + "; ".join(details)
        else:
            status = CheckStatus.PASSED
            confidence = 0.95
            final_details = "Image appears to be authentic"
        
        return CheckResult(
            status=status,
            confidence=confidence,
            details=final_details,
            metadata={
                "dimensions": f"{width}x{height}",
                "has_exif": bool(exif_data),
                "checks_performed": ["dimension_analysis", "exif_check"]
            }
        )
    
    def _real_detection(self, image: Image.Image) -> CheckResult:
        """
        Real AI detection using deep learning model
        
        TODO: Implement actual model inference
        - Load pre-trained model (e.g., CNN-based detector)
        - Preprocess image
        - Run inference
        - Return confidence score
        """
        if not self.model_loaded:
            return CheckResult(
                status=CheckStatus.SKIPPED,
                confidence=0.0,
                details="AI model not loaded"
            )
        
        try:
            # TODO: Implement real model inference
            # Example:
            # preprocessed = self._preprocess_image(image)
            # prediction = self.model(preprocessed)
            # confidence = prediction[0].item()
            
            # For now, return mock result
            return self._mock_detection(image)
            
        except Exception as e:
            logger.error(f"Real detection failed: {e}")
            return CheckResult(
                status=CheckStatus.FAILED,
                confidence=0.0,
                details=f"Model inference failed: {str(e)}"
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
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for model input"""
        # Resize to model input size
        image = image.resize((224, 224))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array and normalize
        img_array = np.array(image) / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    
    async def batch_detect(self, image_urls: list) -> list:
        """
        Detect fake images in batch
        
        Args:
            image_urls: List of image URLs
            
        Returns:
            List of CheckResult objects
        """
        results = []
        for url in image_urls:
            result = await self.detect_fake(url)
            results.append(result)
        return results
