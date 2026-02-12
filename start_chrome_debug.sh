#!/bin/bash
# Helper script to start Chrome with remote debugging

echo "🌐 Starting Chrome with Remote Debugging..."
echo "This will allow the automation to connect to your existing browser session"
echo ""

# Kill existing Chrome instances
pkill -f "chrome.*remote-debugging-port"

# Start Chrome with remote debugging
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile \
  "http://192.1.150.45:4200/#/content-contributor/path/topic-content/48619830-598a-46e1-874f-e85bb4cd312a/e1fa5e65-66d7-4524-874c-95669015ac9f/bc318d6e-13e4-4370-b7a5-0bd7197030bf/en/question-bank" \
  &

echo ""
echo "✅ Chrome started on port 9222"
echo "📝 Please log in if needed, then run: python3 test_video_generation.py"
