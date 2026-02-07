"""
Pydantic models for AI Verification Service
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class VerificationStatus(str, Enum):
    """Verification status enum"""
    PENDING = "PENDING"
    REVIEWING = "REVIEWING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class CheckStatus(str, Enum):
    """Individual check status"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


class VerificationType(str, Enum):
    """Type of verification"""
    INITIAL = "INITIAL"
    CROSS_VERIFICATION = "CROSS_VERIFICATION"
    REVALIDATION = "REVALIDATION"


# ================================
# Request Models
# ================================

class LocationData(BaseModel):
    """Location information"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None


class InitialVerificationRequest(BaseModel):
    """Request for initial issue verification"""
    issue_id: int
    image_urls: List[str] = Field(..., min_items=1, max_items=10)
    category: str
    location: LocationData
    description: str
    metadata: Optional[Dict[str, Any]] = None


class CrossVerificationRequest(BaseModel):
    """Request for cross-verification (citizen vs government)"""
    issue_id: int
    citizen_images: List[str] = Field(..., min_items=1)
    government_images: List[str] = Field(..., min_items=1)
    location: LocationData
    issue_category: str
    metadata: Optional[Dict[str, Any]] = None


class RevalidationRequest(BaseModel):
    """Request to revalidate an existing issue"""
    issue_id: int
    reason: Optional[str] = None


# ================================
# Response Models
# ================================

class CheckResult(BaseModel):
    """Result of an individual check"""
    status: CheckStatus
    confidence: float = Field(..., ge=0, le=1)
    details: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class VerificationChecks(BaseModel):
    """All verification checks performed"""
    fake_detection: CheckResult
    duplicate_detection: CheckResult
    metadata_validation: CheckResult
    location_consistency: CheckResult
    category_relevance: CheckResult
    internet_search: Optional[CheckResult] = None


class InitialVerificationResponse(BaseModel):
    """Response for initial verification"""
    issue_id: int
    status: VerificationStatus
    confidence_score: float = Field(..., ge=0, le=1)
    checks: VerificationChecks
    rejection_reasons: List[str] = []
    warnings: List[str] = []
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CrossVerificationResponse(BaseModel):
    """Response for cross-verification"""
    issue_id: int
    status: VerificationStatus
    confidence_score: float = Field(..., ge=0, le=1)
    same_location: bool
    work_completed: bool
    image_similarity_score: float = Field(..., ge=0, le=1)
    notes: str
    warnings: List[str] = []
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VerificationStatusResponse(BaseModel):
    """Response for verification status query"""
    issue_id: int
    verification_type: VerificationType
    status: VerificationStatus
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    checks_performed: Optional[Dict[str, Any]] = None


# ================================
# Internal Models
# ================================

class ImageAnalysisResult(BaseModel):
    """Result of image analysis"""
    is_fake: bool
    fake_confidence: float
    is_duplicate: bool
    duplicate_confidence: float
    has_valid_metadata: bool
    location_match: bool
    category_match: bool
    category_confidence: float
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}


class ComparisonResult(BaseModel):
    """Result of image comparison"""
    similarity_score: float
    same_location: bool
    location_distance_meters: float
    work_appears_completed: bool
    confidence: float
    notes: str
    warnings: List[str] = []


# ================================
# Health & Stats Models
# ================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str]


class StatsResponse(BaseModel):
    """Verification statistics"""
    total_verifications: int
    approved: int
    rejected: int
    pending: int
    average_confidence: float
    average_processing_time_ms: int
    uptime_seconds: int
