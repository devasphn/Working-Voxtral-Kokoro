#!/bin/bash
# Installation script for Kokoro TTS dependencies
# Adds speech-to-speech capabilities to Voxtral streaming system

echo "=== Installing Kokoro TTS for Speech-to-Speech Functionality ==="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the project root directory."
    exit 1
fi

# Install system dependencies for espeak-ng (required by Kokoro)
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y espeak-ng

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install kokoro>=0.9.4
pip install misaki[en]>=0.3.0
pip install soundfile>=0.12.1

# Verify installation
echo "🧪 Testing Kokoro installation..."
python3 -c "
try:
    from kokoro import KPipeline
    print('✅ Kokoro TTS successfully installed')
    
    # Test basic functionality
    pipeline = KPipeline(lang_code='a')
    print('✅ Kokoro pipeline initialized successfully')
    
    # Test with short text
    test_text = 'Hello, this is a test.'
    generator = pipeline(test_text, voice='af_heart')
    
    for i, (gs, ps, audio) in enumerate(generator):
        if audio is not None and len(audio) > 0:
            print(f'✅ Audio generation test successful: {len(audio)} samples')
            break
    else:
        print('⚠️  Audio generation test returned empty audio')
        
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
except Exception as e:
    print(f'❌ Test error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Kokoro TTS installation completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Update your config.yaml to enable speech-to-speech:"
    echo "   speech_to_speech:"
    echo "     enabled: true"
    echo ""
    echo "2. Start the enhanced server:"
    echo "   ./run_realtime.sh"
    echo ""
    echo "3. Test speech-to-speech functionality by sending WebSocket messages with:"
    echo "   {\"type\": \"audio\", \"mode\": \"speech_to_speech\", \"audio_data\": \"<base64_audio>\"}"
    echo ""
    echo "🗣️ Speech-to-Speech conversational AI is now ready!"
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
