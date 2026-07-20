#!/bin/bash
# Quick test to verify port configuration is working

echo "Testing port configuration..."
echo ""

# Test 1: Check config.js exists
if [ -f "frontend/js/config.js" ]; then
  echo "✓ frontend/js/config.js exists"
else
  echo "✗ frontend/js/config.js missing"
  exit 1
fi

# Test 2: Check no hardcoded 8000 in frontend JS (except timeout values)
HARDCODED=$(grep -r "127\.0\.0\.1:8" frontend/js/*.js | grep -v config.js | grep -v "timeout" | wc -l)
if [ "$HARDCODED" -eq "0" ]; then
  echo "✓ No hardcoded backend ports in frontend JS"
else
  echo "✗ Found hardcoded backend ports in frontend JS:"
  grep -r "127\.0\.0\.1:8" frontend/js/*.js | grep -v config.js | grep -v "timeout"
  exit 1
fi

# Test 3: Check HTML files include config.js
HTML_WITH_CONFIG=$(grep -l "config.js" frontend/*.html | wc -l)
HTML_TOTAL=$(ls frontend/*.html 2>/dev/null | wc -l)
if [ "$HTML_WITH_CONFIG" -eq "$HTML_TOTAL" ]; then
  echo "✓ All HTML files include config.js"
else
  echo "⚠ Some HTML files may not include config.js"
  echo "  Files with config.js: $HTML_WITH_CONFIG"
  echo "  Total HTML files: $HTML_TOTAL"
fi

# Test 4: Check startup scripts are executable
if [ -x "start-backend.sh" ] && [ -x "start-frontend.sh" ]; then
  echo "✓ Startup scripts are executable"
else
  echo "⚠ Startup scripts may not be executable (run: chmod +x start-*.sh)"
fi

# Test 5: Check .env.example has PORT variable
if grep -q "^PORT=" backend/.env.example; then
  echo "✓ backend/.env.example has PORT variable"
else
  echo "✗ backend/.env.example missing PORT variable"
  exit 1
fi

echo ""
echo "All checks passed! ✨"
echo ""
echo "To use custom ports:"
echo "  1. Backend: Edit backend/.env and set PORT=8003"
echo "  2. Frontend: python3 -m http.server 3003"
echo "  3. Visit: http://127.0.0.1:3003/login.html?backend_port=8003"
