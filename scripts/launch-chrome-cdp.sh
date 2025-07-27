#!/bin/bash

# Launch Chrome with CDP for StarHTML development

echo "🌐 Launching Chrome with CDP enabled..."

# Standard port for all StarHTML demos (using 5001 to avoid conflicts)
APP_PORT=5001
echo "🚀 Targeting http://localhost:$APP_PORT"

# Create temp directory for Chrome profile
CHROME_USER_DATA_DIR="/tmp/chrome-debug-starhtml"
rm -rf "$CHROME_USER_DATA_DIR"
mkdir -p "$CHROME_USER_DATA_DIR"

# Launch Chrome with CDP
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --remote-debugging-address=127.0.0.1 \
    --user-data-dir="$CHROME_USER_DATA_DIR" \
    --no-first-run \
    --disable-default-apps \
    --disable-gpu \
    --disable-features=VoiceTranscription \
    --window-size=1280,800 \
    http://localhost:$APP_PORT &

CHROME_PID=$!
echo "✅ Chrome launched with PID: $CHROME_PID"
echo "🔧 CDP available at: http://127.0.0.1:9222"
echo "📱 StarHTML app: http://localhost:$APP_PORT"

# Store PID for cleanup
echo $CHROME_PID > .chrome-cdp.pid

# Monitor Chrome process
while true; do
    if ! kill -0 $CHROME_PID 2>/dev/null; then
        echo "⚠️ Chrome process ended (PID: $CHROME_PID)"
        exit_code=$?
        echo "Exit code: $exit_code"
        
        # Wait a moment before potentially restarting
        sleep 2
        
        echo "🔄 Chrome has exited. Process complete."
        exit $exit_code
    fi
    sleep 5
done