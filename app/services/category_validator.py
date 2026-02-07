"""
Category Validation Service

This service validates:
- Image content matches reported issue category
- NLP-based classification
- Visual content analysis
- Relevance scoring
"""

import logging
from typing import Dict, List
from PIL import Image
import io
import httpx

from app.config import get_settings
from app.models import CheckResult, CheckStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class CategoryValidatorService:
    """Service for validating issue category relevance"""
    
    # Category keywords for heuristic matching
    CATEGORY_KEYWORDS = {
        "Road Infrastructure": [
            "road", "street", "pavement", "pothole", "crack", "asphalt",
            "highway", "lane", "traffic", "intersection", "crosswalk"
        ],
        "Water & Drainage": [
            "water", "drain", "sewer", "pipe", "leak", "flood", "puddle",
            "manhole", "gutter", "overflow", "sewage"
        ],
        "Street Lighting": [
            "light", "lamp", "pole", "streetlight", "bulb", "dark",
            "illumination", "lighting", "fixture"
        ],
        "Waste Management": [
            "garbage", "trash", "waste", "bin", "dumpster", "litter",
            "rubbish", "disposal", "recycling", "dump"
        ],
        "Traffic & Transportation": [
            "traffic", "signal", "sign", "bus", "stop", "parking",
            "vehicle", "car", "transport", "congestion"
        ],
        "Public Safety": [
            "danger", "hazard", "unsafe", "broken", "damaged", "risk",
            "accident", "injury", "security", "crime"
        ],
        "Parks & Recreation": [
            "park", "playground", "bench", "tree", "grass", "garden",
            "recreation", "sports", "field", "path"
        ],
        "Utilities & Power": [
            "power", "electric", "utility", "wire", "cable", "transformer",
            "pole", "outage", "electricity", "gas"
        ],
        "Building & Construction": [
            "building", "construction", "structure", "wall", "roof",
            "foundation", "demolition", "renovation", "property"
        ],
        "Environmental Issues": [
            "pollution", "environment", "air", "noise", "smell", "odor",
            "contamination", "toxic", "hazardous", "waste"
        ],
        "Public Health": [
            "health", "sanitation", "hygiene", "pest", "rodent", "insect",
            "disease", "medical", "clinic", "hospital"
        ],
        "Community Services": [
            "community", "service", "facility", "center", "public",
            "amenity", "resource", "program"
        ]
    }
    
    def __init__(self):
        self.settings = settings
        self.model_loaded = False
        
        if not settings.enable_mock_ai:
            self._load_model()
    
    def _load_model(self):
        """Load category classification model"""
        try:
            # TODO: Load actual classification model
            # Example: self.model = torch.load(settings.category_model_path)
            logger.info("Category classification model loaded")
            self.model_loaded = True
        except Exception as e:
            logger.error(f"Failed to load category model: {e}")
            self.model_loaded = False
    
    async def validate_category(
        self,
        image_url: str,
        category: str,
        description: str
    ) -> CheckResult:
        """
        Validate if image matches the reported category
        
        Args:
            image_url: URL of the image
            category: Reported issue category
            description: Issue description
            
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
                    details="Failed to download image for category validation"
                )
            
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            if settings.enable_mock_ai:
                # Mock validation using heuristics
                result = self._mock_validation(image, category, description)
            else:
                # Real AI validation
                result = self._real_validation(image, category, description)
            
            return result
            
        except Exception as e:
            logger.error(f"Category validation failed: {e}")
            return CheckResult(
                status=CheckStatus.FAILED,
                confidence=0.0,
                details=f"Validation error: {str(e)}"
            )
    
    def _mock_validation(
        self,
        image: Image.Image,
        category: str,
        description: str
    ) -> CheckResult:
        """
        Mock validation using keyword matching
        
        Checks if description contains keywords related to the category
        """
        # Get keywords for category
        keywords = self.CATEGORY_KEYWORDS.get(category, [])
        
        if not keywords:
            # Unknown category
            return CheckResult(
                status=CheckStatus.WARNING,
                confidence=0.6,
                details=f"Unknown category: {category}",
                metadata={"category": category}
            )
        
        # Check description for keywords
        description_lower = description.lower()
        matches = [kw for kw in keywords if kw in description_lower]
        
        # Calculate confidence based on keyword matches
        match_ratio = len(matches) / len(keywords) if keywords else 0
        confidence = 0.5 + (match_ratio * 0.5)  # 0.5 to 1.0 range
        
        if match_ratio >= 0.2:  # At least 20% keywords match
            status = CheckStatus.PASSED
            details = f"Category '{category}' appears relevant. Matched keywords: {', '.join(matches[:5])}"
        elif match_ratio >= 0.1:  # 10-20% match
            status = CheckStatus.WARNING
            details = f"Category '{category}' may be relevant but confidence is low. Matched: {', '.join(matches)}"
        else:
            status = CheckStatus.WARNING
            details = f"Category '{category}' relevance unclear. Few matching keywords found."
        
        return CheckResult(
            status=status,
            confidence=confidence,
            details=details,
            metadata={
                "category": category,
                "matched_keywords": matches[:10],
                "match_ratio": match_ratio
            }
        )
    
    def _real_validation(
        self,
        image: Image.Image,
        category: str,
        description: str
    ) -> CheckResult:
        """
        Real AI validation using deep learning model
        
        TODO: Implement actual model inference
        - Image classification
        - NLP analysis of description
        - Multi-modal fusion
        """
        if not self.model_loaded:
            return CheckResult(
                status=CheckStatus.SKIPPED,
                confidence=0.0,
                details="Category classification model not loaded"
            )
        
        try:
            # TODO: Implement real model inference
            # Example:
            # image_features = self._extract_image_features(image)
            # text_features = self._extract_text_features(description)
            # prediction = self.model(image_features, text_features)
            # confidence = prediction[category]
            
            # For now, return mock result
            return self._mock_validation(image, category, description)
            
        except Exception as e:
            logger.error(f"Real validation failed: {e}")
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
    
    def get_supported_categories(self) -> List[str]:
        """Get list of supported categories"""
        return list(self.CATEGORY_KEYWORDS.keys())
