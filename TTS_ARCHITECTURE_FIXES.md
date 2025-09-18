# TTS System Architecture Fixes

## 🚨 Critical Issues Identified and Fixed

### Problem Summary
The system was failing during model verification due to:
1. **Mock attribute errors**: `'OrpheusPerfectModel' object has no attribute 'use_mock'`
2. **Mock model cleanup errors**: `'OrpheusPerfectModel' object has no attribute 'mock_model'`
3. **Forced Orpheus initialization**: System always tried to initialize Orpheus even when Kokoro should be sufficient
4. **Incorrect TTS hierarchy**: No proper conditional logic for Kokoro-primary, Orpheus-fallback

## ✅ Comprehensive Fixes Applied

### 1. **Fixed OrpheusPerfectModel Mock Attribute Errors**

**File**: `src/tts/orpheus_perfect_model.py`

**Issue**: References to non-existent `use_mock` and `mock_model` attributes
**Fix**: Removed all mock-related code and replaced with proper TTS engine tracking

**Before (BROKEN)**:
```python
def get_model_info(self):
    perfect_info = {
        "using_mock": self.use_mock,  # ❌ Attribute doesn't exist
        # ...
    }

async def cleanup(self):
    if self.mock_model:  # ❌ Attribute doesn't exist
        await self.mock_model.cleanup()
```

**After (FIXED)**:
```python
def get_model_info(self):
    perfect_info = {
        "tts_engine": "kokoro" if self.use_kokoro else "orpheus" if self.streaming_model else "none",  # ✅ Proper engine tracking
        # ...
    }

async def cleanup(self):
    if self.kokoro_model:  # ✅ Proper model references
        self.kokoro_model = None
    if self.streaming_model:
        await self.streaming_model.cleanup()
        self.streaming_model = None
```

### 2. **Implemented Conditional TTS Initialization in Unified Model Manager**

**File**: `src/models/unified_model_manager.py`

**Issue**: System always initialized Orpheus regardless of Kokoro success
**Fix**: Replaced forced Orpheus initialization with conditional TTS hierarchy

**Before (BROKEN)**:
```python
async def initialize(self):
    await self._initialize_voxtral_model()
    await self._initialize_orpheus_model()  # ❌ Always initializes Orpheus
```

**After (FIXED)**:
```python
async def initialize(self):
    await self._initialize_voxtral_model()
    await self._initialize_tts_model()  # ✅ Conditional TTS initialization

async def _initialize_tts_model(self):
    """Initialize TTS model with Kokoro-primary, Orpheus-fallback hierarchy"""
    # OrpheusPerfectModel handles the hierarchy internally
    self.orpheus_model = OrpheusPerfectModel()
    success = await self.orpheus_model.initialize()
    
    # Check which engine was actually used
    model_info = self.orpheus_model.get_model_info()
    tts_engine = model_info.get("tts_engine", "unknown")
    unified_logger.info(f"✅ TTS model initialized with {tts_engine} engine")
```

### 3. **Enhanced TTS Engine Verification**

**Before (BROKEN)**:
```python
# Test Orpheus model
if self.orpheus_model and self.orpheus_model.is_initialized:
    model_info = self.orpheus_model.get_model_info()
    if not model_info.get("is_initialized"):
        raise ModelInitializationError("Orpheus model verification failed")  # ❌ Generic error
```

**After (FIXED)**:
```python
# Test TTS model (Kokoro/Orpheus)
if self.orpheus_model and self.orpheus_model.is_initialized:
    model_info = self.orpheus_model.get_model_info()
    if not model_info.get("is_initialized"):
        raise ModelInitializationError("TTS model verification failed")
    
    tts_engine = model_info.get("tts_engine", "unknown")
    unified_logger.info(f"✅ TTS model verification passed (using {tts_engine} engine)")  # ✅ Engine-specific logging
```

## 🎯 System Architecture After Fixes

### Correct TTS Hierarchy Flow:

```
1. System starts
2. UnifiedModelManager._initialize_tts_model() called
3. Creates OrpheusPerfectModel()
4. OrpheusPerfectModel.initialize() tries Kokoro first:
   
   SUCCESS PATH (Kokoro Primary):
   ├── Kokoro TTS initializes successfully ✅
   ├── use_kokoro = True
   ├── streaming_model = None
   ├── TTS engine = "kokoro"
   └── No Orpheus initialization needed ✅
   
   FALLBACK PATH (Orpheus Fallback):
   ├── Kokoro TTS fails ❌
   ├── Falls back to Orpheus TTS
   ├── use_kokoro = False
   ├── streaming_model = OrpheusStreamingModel()
   ├── TTS engine = "orpheus"
   └── Orpheus initialization occurs ✅
```

### Model State Management:

**Kokoro Primary State**:
- `use_kokoro = True`
- `kokoro_model = KokoroTTSModel()`
- `streaming_model = None`
- `tts_engine = "kokoro"`

**Orpheus Fallback State**:
- `use_kokoro = False`
- `kokoro_model = None`
- `streaming_model = OrpheusStreamingModel()`
- `tts_engine = "orpheus"`

## 🔧 Key Benefits

### 1. **Eliminates Attribute Errors**
- ✅ No more `'use_mock'` attribute errors
- ✅ No more `'mock_model'` attribute errors
- ✅ Clean model info without mock references

### 2. **Proper Resource Management**
- ✅ Only initializes necessary TTS engine
- ✅ Reduces memory usage when Kokoro works
- ✅ Faster startup with lightweight Kokoro
- ✅ Proper cleanup of model references

### 3. **Clear Engine Separation**
- ✅ Mutually exclusive TTS engines
- ✅ Clear logging of which engine is active
- ✅ Proper fallback mechanism
- ✅ No mock service dependencies

### 4. **Improved Error Handling**
- ✅ Engine-specific error messages
- ✅ Proper verification of active engine
- ✅ Clear distinction between Kokoro and Orpheus failures

## 🧪 Testing and Validation

### Run the comprehensive test:
```bash
python3 test_architecture_fixes.py
```

### Expected results:
```
✅ OrpheusPerfectModel Mock Attributes: PASSED
✅ get_model_info() Method: PASSED
✅ cleanup() Method: PASSED
✅ TTS Hierarchy Initialization: PASSED
✅ Unified Model Manager Integration: PASSED

🎉 All architecture fixes validated successfully!
```

### Start your system:
```bash
python3 -m src.api.ui_server_realtime
```

### Expected behavior:
- No more mock attribute errors
- Proper TTS engine initialization (Kokoro first, Orpheus fallback)
- Clear logging of which TTS engine is being used
- Successful model verification without errors

## 📊 System Performance Impact

### Before Fixes:
- ❌ Always initialized both Kokoro and Orpheus
- ❌ Wasted memory on unused engines
- ❌ Slower startup due to unnecessary initialization
- ❌ Confusing error messages about mock services

### After Fixes:
- ✅ Initializes only the needed TTS engine
- ✅ Optimal memory usage (Kokoro: ~82M params vs Orpheus: ~3B params)
- ✅ Faster startup with Kokoro primary
- ✅ Clear, engine-specific logging and error messages

## 🚀 Production Benefits

1. **Reliability**: No more crashes due to missing mock attributes
2. **Performance**: Reduced memory usage and faster initialization
3. **Maintainability**: Clean separation between TTS engines
4. **Debugging**: Clear logging of TTS engine selection and status
5. **Scalability**: Proper resource management for production deployment

Your TTS system now implements a clean Kokoro-primary, Orpheus-fallback architecture without any mock service dependencies! 🎉
