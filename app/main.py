"""
CivicFix AI Verification Service - Main Application

FastAPI application for AI-driven verification of civic issues
"""

import logging
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db, init_db, check_db_connection
from app.models import (
    InitialVerificationRequest,
    InitialVerificationResponse,
    CrossVerificationRequest,
    CrossVerificationResponse,
    RevalidationRequest,
    VerificationStatusResponse,
    HealthResponse,
    StatsResponse,
    VerificationStatus,
    VerificationType,
    CheckResult,
    CheckStatus,
    VerificationChecks
)
from app.services import (
    FakeDetectionService,
    DuplicateDetectionService,
    MetadataValidatorService,
    LocationValidatorService,
    CategoryValidatorService,
    CrossVerificationService,
    InternetSearchService
)
from app.database import (
    save_verification_result,
    create_timeline_event,
    get_verification_by_issue_id
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Service start time for uptime tracking
SERVICE_START_TIME = time.time()

# Statistics tracking
stats = {
    "total_verifications": 0,
    "approved": 0,
    "rejected": 0,
    "pending": 0,
    "total_processing_time_ms": 0
}


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting CivicFix AI Verification Service...")
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CivicFix AI Verification Service...")


# Create FastAPI app
app = FastAPI(
    title="CivicFix AI Verification Service",
    description="AI-driven verification for civic issue reporting",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = settings.allowed_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
fake_detection_service = FakeDetectionService()
duplicate_detection_service = DuplicateDetectionService()
metadata_validator_service = MetadataValidatorService()
location_validator_service = LocationValidatorService()
category_validator_service = CategoryValidatorService()
cross_verification_service = CrossVerificationService()
internet_search_service = InternetSearchService()


# ================================
# Authentication
# ================================

async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key"""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ================================
# Health & Monitoring
# ================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_status = "healthy" if check_db_connection() else "unhealthy"
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services={
            "database": db_status,
            "fake_detection": "enabled" if settings.fake_detection_enabled else "disabled",
            "duplicate_detection": "enabled" if settings.duplicate_detection_enabled else "disabled",
            "location_validation": "enabled" if settings.location_validation_enabled else "disabled",
            "category_validation": "enabled" if settings.category_validation_enabled else "disabled"
        }
    )


@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Get verification statistics"""
    uptime = int(time.time() - SERVICE_START_TIME)
    avg_processing_time = (
        stats["total_processing_time_ms"] // stats["total_verifications"]
        if stats["total_verifications"] > 0
        else 0
    )
    avg_confidence = 0.85  # TODO: Calculate from database
    
    return StatsResponse(
        total_verifications=stats["total_verifications"],
        approved=stats["approved"],
        rejected=stats["rejected"],
        pending=stats["pending"],
        average_confidence=avg_confidence,
        average_processing_time_ms=avg_processing_time,
        uptime_seconds=uptime
    )


# ================================
# Verification Endpoints
# ================================

@app.post("/api/v1/verify/initial", response_model=InitialVerificationResponse)
async def verify_initial_issue(
    request: InitialVerificationRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Verify newly submitted issue
    
    Performs comprehensive verification:
    - Fake/AI-generated image detection
    - Duplicate image detection
    - Metadata validation
    - Location consistency check
    - Category relevance validation
    - Internet image search (optional)
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting initial verification for issue #{request.issue_id}")
        
        # Run all verification checks
        checks_results = {}
        
        # 1. Fake Detection
        if settings.fake_detection_enabled:
            fake_results = await fake_detection_service.batch_detect(request.image_urls)
            # Use worst result
            fake_check = min(fake_results, key=lambda x: x.confidence)
            checks_results["fake_detection"] = fake_check
        else:
            checks_results["fake_detection"] = CheckResult(
                status=CheckStatus.SKIPPED,
                confidence=0.0,
                details="Fake detection disabled"
            )
        
        # 2. Duplicate Detection
        if settings.duplicate_detection_enabled:
            dup_results = await duplicate_detection_service.batch_detect(
                request.image_urls,
                request.issue_id
            )
            # Use worst result
            dup_check = min(dup_results, key=lambda x: x.confidence)
            checks_results["duplicate_detection"] = dup_check
        else:
            checks_results["duplicate_detection"] = CheckResult(
                status=CheckStatus.SKIPPED,
                confidence=0.0,
                details="Duplicate detection disabled"
            )
        
        # 3. Metadata Validation
        metadata_check = await metadata_validator_service.validate_metadata(
            request.image_urls[0]
        )
        checks_results["metadata_validation"] = metadata_check
        
        # 4. Location Consistency
        if settings.location_validation_enabled:
            location_check = await location_validator_service.validate_location(
                request.image_urls[0],
                request.location
            )
            checks_results["location_consistency"] = location_check
        else:
            checks_results["location_consistency"] = CheckResult(
                status=CheckStatus.SKIPPED,
                confidence=0.0,
                details="Location validation disabled"
            )
        
        # 5. Category Relevance
        if settings.category_validation_enabled:
            category_check = await category_validator_service.validate_category(
                request.image_urls[0],
                request.category,
                request.description
            )
            checks_results["category_relevance"] = category_check
        else:
            checks_results["category_relevance"] = CheckResult(
                status=CheckStatus.SKIPPED,
                confidence=0.0,
                details="Category validation disabled"
            )
        
        # 6. Internet Search (optional)
        if settings.enable_internet_search:
            internet_check = await internet_search_service.search_image(
                request.image_urls[0]
            )
            checks_results["internet_search"] = internet_check
        
        # Create VerificationChecks object
        checks = VerificationChecks(**checks_results)
        
        # Calculate overall confidence and status
        confidence_score, status, rejection_reasons, warnings = _calculate_overall_result(checks)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Save to database
        save_verification_result(
            db=db,
            issue_id=request.issue_id,
            verification_type=VerificationType.INITIAL,
            status=status,
            confidence_score=confidence_score,
            rejection_reasons=rejection_reasons,
            checks_performed={
                "fake_detection": checks.fake_detection.dict(),
                "duplicate_detection": checks.duplicate_detection.dict(),
                "metadata_validation": checks.metadata_validation.dict(),
                "location_consistency": checks.location_consistency.dict(),
                "category_relevance": checks.category_relevance.dict()
            }
        )
        
        # Create timeline event
        create_timeline_event(
            db=db,
            issue_id=request.issue_id,
            event_type="AI_VERIFICATION_COMPLETED",
            actor_type="AI",
            description=f"AI verification completed with status: {status}",
            metadata={
                "confidence_score": confidence_score,
                "status": status,
                "processing_time_ms": processing_time_ms
            }
        )
        
        # Update statistics
        stats["total_verifications"] += 1
        stats["total_processing_time_ms"] += processing_time_ms
        if status == VerificationStatus.APPROVED:
            stats["approved"] += 1
        elif status == VerificationStatus.REJECTED:
            stats["rejected"] += 1
        else:
            stats["pending"] += 1
        
        logger.info(
            f"Verification completed for issue #{request.issue_id}: "
            f"status={status}, confidence={confidence_score:.2f}, time={processing_time_ms}ms"
        )
        
        return InitialVerificationResponse(
            issue_id=request.issue_id,
            status=status,
            confidence_score=confidence_score,
            checks=checks,
            rejection_reasons=rejection_reasons,
            warnings=warnings,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        logger.error(f"Verification failed for issue #{request.issue_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.post("/api/v1/verify/cross-check", response_model=CrossVerificationResponse)
async def verify_cross_check(
    request: CrossVerificationRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Cross-verify citizen vs government images
    
    Compares "before" and "after" images to verify:
    - Same location
    - Actual work completion
    - Legitimate resolution
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting cross-verification for issue #{request.issue_id}")
        
        # Perform cross-verification
        result = await cross_verification_service.verify_resolution(
            citizen_images=request.citizen_images,
            government_images=request.government_images,
            location=request.location,
            issue_category=request.issue_category
        )
        
        # Determine status based on results
        if result.confidence >= settings.auto_approve_threshold and result.work_appears_completed:
            status = VerificationStatus.APPROVED
        elif result.confidence <= settings.auto_reject_threshold or not result.same_location:
            status = VerificationStatus.REJECTED
        else:
            status = VerificationStatus.NEEDS_REVIEW
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Save to database
        save_verification_result(
            db=db,
            issue_id=request.issue_id,
            verification_type=VerificationType.CROSS_VERIFICATION,
            status=status,
            confidence_score=result.confidence,
            rejection_reasons=result.warnings,
            checks_performed={
                "same_location": result.same_location,
                "work_completed": result.work_appears_completed,
                "similarity_score": result.similarity_score
            }
        )
        
        # Create timeline event
        create_timeline_event(
            db=db,
            issue_id=request.issue_id,
            event_type="AI_CROSS_VERIFICATION_COMPLETED",
            actor_type="AI",
            description=f"Cross-verification completed: {result.notes}",
            metadata={
                "confidence": result.confidence,
                "status": status,
                "work_completed": result.work_appears_completed
            }
        )
        
        logger.info(
            f"Cross-verification completed for issue #{request.issue_id}: "
            f"status={status}, confidence={result.confidence:.2f}"
        )
        
        return CrossVerificationResponse(
            issue_id=request.issue_id,
            status=status,
            confidence_score=result.confidence,
            same_location=result.same_location,
            work_completed=result.work_appears_completed,
            image_similarity_score=result.similarity_score,
            notes=result.notes,
            warnings=result.warnings,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        logger.error(f"Cross-verification failed for issue #{request.issue_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Cross-verification failed: {str(e)}")


@app.get("/api/v1/verify/status/{issue_id}", response_model=VerificationStatusResponse)
async def get_verification_status(
    issue_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get verification status for an issue"""
    try:
        verification = get_verification_by_issue_id(db, issue_id)
        
        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")
        
        return VerificationStatusResponse(
            issue_id=verification.issue_id,
            verification_type=verification.verification_type,
            status=verification.status,
            confidence_score=verification.confidence_score,
            created_at=verification.created_at,
            updated_at=verification.created_at,
            checks_performed=verification.checks_performed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get verification status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================================
# Helper Functions
# ================================

def _calculate_overall_result(checks: VerificationChecks) -> tuple:
    """
    Calculate overall verification result
    
    Returns:
        (confidence_score, status, rejection_reasons, warnings)
    """
    # Collect all check results
    all_checks = [
        checks.fake_detection,
        checks.duplicate_detection,
        checks.metadata_validation,
        checks.location_consistency,
        checks.category_relevance
    ]
    
    if checks.internet_search:
        all_checks.append(checks.internet_search)
    
    # Filter out skipped checks
    active_checks = [c for c in all_checks if c.status != CheckStatus.SKIPPED]
    
    if not active_checks:
        return 0.5, VerificationStatus.NEEDS_REVIEW, ["No checks performed"], []
    
    # Calculate average confidence
    confidence_score = sum(c.confidence for c in active_checks) / len(active_checks)
    
    # Collect failures and warnings
    failures = [c for c in active_checks if c.status == CheckStatus.FAILED]
    warnings_list = [c for c in active_checks if c.status == CheckStatus.WARNING]
    
    rejection_reasons = [c.details for c in failures]
    warnings = [c.details for c in warnings_list]
    
    # Determine status
    if failures:
        status = VerificationStatus.REJECTED
    elif confidence_score >= settings.auto_approve_threshold:
        status = VerificationStatus.APPROVED
    elif confidence_score <= settings.auto_reject_threshold:
        status = VerificationStatus.REJECTED
    else:
        status = VerificationStatus.NEEDS_REVIEW
    
    return confidence_score, status, rejection_reasons, warnings


# ================================
# Root Endpoint
# ================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CivicFix AI Verification Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=settings.debug
    )
