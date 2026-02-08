"""
Configuration management for AI Verification Service
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    service_name: str = "civicfix-ai-service"
    service_port: int = 8001
    debug: bool = False
    log_level: str = "INFO"
    
    # Database
    database_url: str
    
    # AI Models
    fake_detection_model_path: str = "models/fake_detector.pth"
    fake_detection_enabled: bool = True
    
    duplicate_threshold: float = 0.85
    duplicate_detection_enabled: bool = True
    
    location_radius_meters: float = 100.0
    location_validation_enabled: bool = True
    
    category_validation_enabled: bool = True
    category_model_path: str = "models/category_classifier.pth"
    
    # Confidence Thresholds
    min_confidence_score: float = 0.7
    auto_approve_threshold: float = 0.9
    auto_reject_threshold: float = 0.3
    
    # External APIs
    google_vision_api_key: Optional[str] = None
    google_vision_enabled: bool = False
    
    reverse_image_search_api_key: Optional[str] = None
    reverse_image_search_enabled: bool = False
    
    # Security
    api_key: str
    secret_key: str
    allowed_origins: str = "http://localhost:3000,http://localhost:5000"
    
    # Performance & Limits
    max_image_size_mb: int = 10
    max_images_per_request: int = 10
    request_timeout_seconds: int = 30
    max_concurrent_requests: int = 10
    
    # Caching
    redis_url: Optional[str] = None
    cache_enabled: bool = False
    cache_ttl_seconds: int = 3600
    
    # Monitoring
    prometheus_enabled: bool = True
    sentry_dsn: Optional[str] = None
    sentry_enabled: bool = False
    
    # Feature Flags
    enable_mock_ai: bool = True
    enable_internet_search: bool = False
    enable_advanced_analysis: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
