"""
Unit tests for AI verification services
"""

import pytest
from PIL import Image
import io

from app.services.fake_detection import FakeDetectionService
from app.services.duplicate_detection import DuplicateDetectionService
from app.services.metadata_validator import MetadataValidatorService
from app.services.location_validator import LocationValidatorService
from app.services.category_validator import CategoryValidatorService
from app.models import LocationData, CheckStatus


@pytest.fixture
def fake_detection_service():
    return FakeDetectionService()


@pytest.fixture
def duplicate_detection_service():
    return DuplicateDetectionService()


@pytest.fixture
def metadata_validator_service():
    return MetadataValidatorService()


@pytest.fixture
def location_validator_service():
    return LocationValidatorService()


@pytest.fixture
def category_validator_service():
    return CategoryValidatorService()


@pytest.fixture
def sample_image():
    """Create a sample image for testing"""
    img = Image.new('RGB', (512, 512), color='red')
    return img


class TestFakeDetectionService:
    """Tests for fake detection service"""
    
    def test_mock_detection_square_image(self, fake_detection_service, sample_image):
        """Test mock detection with square image"""
        result = fake_detection_service._mock_detection(sample_image)
        assert result.status in [CheckStatus.PASSED, CheckStatus.WARNING]
        assert 0 <= result.confidence <= 1
    
    def test_mock_detection_non_square_image(self, fake_detection_service):
        """Test mock detection with non-square image"""
        img = Image.new('RGB', (800, 600), color='blue')
        result = fake_detection_service._mock_detection(img)
        assert result.status == CheckStatus.PASSED
        assert result.confidence > 0.8


class TestDuplicateDetectionService:
    """Tests for duplicate detection service"""
    
    def test_no_duplicate_first_image(self, duplicate_detection_service, sample_image):
        """Test first image has no duplicates"""
        # Calculate hash
        phash = duplicate_detection_service._calculate_phash(sample_image)
        
        # Check duplicates (should be none)
        is_dup, similarity, issue_id = duplicate_detection_service._check_duplicates(phash, None)
        assert not is_dup
        assert similarity == 0.0
    
    def test_duplicate_detection_same_image(self, duplicate_detection_service, sample_image):
        """Test duplicate detection with same image"""
        # Calculate hash and store
        phash = duplicate_detection_service._calculate_phash(sample_image)
        duplicate_detection_service._store_hash(phash, 1)
        
        # Check again (should find duplicate)
        is_dup, similarity, issue_id = duplicate_detection_service._check_duplicates(phash, 2)
        assert is_dup
        assert similarity >= 0.85
        assert issue_id == 1
    
    def test_cache_management(self, duplicate_detection_service):
        """Test cache operations"""
        initial_size = duplicate_detection_service.get_cache_size()
        
        # Add some hashes
        img1 = Image.new('RGB', (100, 100), color='red')
        phash1 = duplicate_detection_service._calculate_phash(img1)
        duplicate_detection_service._store_hash(phash1, 1)
        
        assert duplicate_detection_service.get_cache_size() == initial_size + 1
        
        # Clear cache
        duplicate_detection_service.clear_cache()
        assert duplicate_detection_service.get_cache_size() == 0


class TestLocationValidatorService:
    """Tests for location validator service"""
    
    def test_distance_calculation(self, location_validator_service):
        """Test Haversine distance calculation"""
        # Chennai coordinates
        lat1, lon1 = 13.0827, 80.2707
        # Nearby location (approx 1km away)
        lat2, lon2 = 13.0927, 80.2707
        
        distance = location_validator_service._calculate_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 1000-1200 meters
        assert 900 < distance < 1300
    
    def test_validate_coordinates(self, location_validator_service):
        """Test coordinate validation"""
        # Valid coordinates
        assert location_validator_service.validate_coordinates(13.0827, 80.2707)
        assert location_validator_service.validate_coordinates(0, 0)
        assert location_validator_service.validate_coordinates(-90, -180)
        assert location_validator_service.validate_coordinates(90, 180)
        
        # Invalid coordinates
        assert not location_validator_service.validate_coordinates(91, 0)
        assert not location_validator_service.validate_coordinates(0, 181)
        assert not location_validator_service.validate_coordinates(-91, 0)


class TestCategoryValidatorService:
    """Tests for category validator service"""
    
    def test_get_supported_categories(self, category_validator_service):
        """Test getting supported categories"""
        categories = category_validator_service.get_supported_categories()
        assert len(categories) > 0
        assert "Road Infrastructure" in categories
        assert "Water & Drainage" in categories
    
    def test_mock_validation_good_match(self, category_validator_service, sample_image):
        """Test mock validation with good keyword match"""
        result = category_validator_service._mock_validation(
            sample_image,
            "Road Infrastructure",
            "Large pothole on main road causing traffic issues"
        )
        assert result.status == CheckStatus.PASSED
        assert result.confidence > 0.6
    
    def test_mock_validation_poor_match(self, category_validator_service, sample_image):
        """Test mock validation with poor keyword match"""
        result = category_validator_service._mock_validation(
            sample_image,
            "Road Infrastructure",
            "Some random text with no relevant keywords"
        )
        assert result.status == CheckStatus.WARNING
        assert result.confidence < 0.7


class TestMetadataValidatorService:
    """Tests for metadata validator service"""
    
    def test_extract_exif_no_data(self, metadata_validator_service, sample_image):
        """Test EXIF extraction with no data"""
        exif_data = metadata_validator_service._extract_exif(sample_image)
        assert isinstance(exif_data, dict)
        # New image should have no EXIF
        assert len(exif_data) == 0
    
    def test_validate_exif_no_data(self, metadata_validator_service):
        """Test validation with no EXIF data"""
        result = metadata_validator_service._validate_exif_data({})
        assert result.status == CheckStatus.WARNING
        assert result.confidence < 1.0
        assert "No EXIF data" in result.details


# Integration test
@pytest.mark.asyncio
async def test_full_verification_flow():
    """Test complete verification flow"""
    # This would test the full API endpoint
    # Requires running server and test client
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
