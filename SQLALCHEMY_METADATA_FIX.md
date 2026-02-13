# SQLAlchemy Metadata Conflict - FIXED ✅

## Problem

The AI service was crashing on Render deployment with:

```
sqlalchemy.exc.InvalidRequestError:
Attribute name 'metadata' is reserved when using the Declarative API.
```

## Root Cause

Both `AIVerification` and `TimelineEvent` models had a column named `metadata`, which conflicts with SQLAlchemy's reserved `Base.metadata` attribute used for table schema management.

## Solution Applied

### 1. Renamed Model Attributes

Changed the Python attribute name from `metadata` to `extra_data` while keeping the database column name as `metadata` for backward compatibility:

**Before:**
```python
class AIVerification(Base):
    metadata = Column(JSON)
```

**After:**
```python
class AIVerification(Base):
    extra_data = Column("metadata", JSON)  # Map to 'metadata' column in DB
```

### 2. Updated Function Signatures

Changed function parameters from `metadata` to `extra_data`:

- `save_verification_result(extra_data: dict = None)`
- `create_timeline_event(extra_data: dict = None)`

### 3. Updated Function Calls

Updated all calls in `main.py`:

**Before:**
```python
create_timeline_event(
    metadata={"confidence_score": 0.95}
)
```

**After:**
```python
create_timeline_event(
    extra_data={"confidence_score": 0.95}
)
```

## Files Modified

1. ✅ `ai-service/app/database.py`
   - `AIVerification.metadata` → `AIVerification.extra_data`
   - `TimelineEvent.metadata` → `TimelineEvent.extra_data`
   - Function signatures updated

2. ✅ `ai-service/app/main.py`
   - Updated `create_timeline_event()` calls to use `extra_data`

## Database Compatibility

✅ **No database migration needed!**

The database column is still named `metadata`. We only changed the Python attribute name using SQLAlchemy's column mapping:

```python
extra_data = Column("metadata", JSON)
```

This means:
- Existing data remains intact
- No schema changes required
- Backward compatible with existing database

## Testing

After deployment, verify:

```bash
# Test health endpoint
curl https://civicfix-ai-service.onrender.com/health

# Should return:
{
  "status": "healthy",
  "service": "civicfix-ai-service"
}
```

## Deployment

The fix is ready. Redeploy to Render:

1. Push changes to GitHub
2. Render will auto-deploy
3. Service should start successfully

## Prevention

To avoid this issue in the future:

- ❌ Never use `metadata` as a column name in SQLAlchemy models
- ✅ Use alternative names: `extra_data`, `meta_info`, `additional_data`
- ✅ If you must use `metadata` in DB, map it: `extra_data = Column("metadata", JSON)`

## Status

🟢 **FIXED** - Ready for deployment
