#!/bin/bash
# ============================================================================
# Generate Secure API Key for Render Deployment
# ============================================================================
# 
# Usage: ./generate_api_key.sh
#
# This generates a cryptographically secure random API key suitable for
# protecting /api/copilot/question and /api/metrics endpoints.
#
# ============================================================================

echo "🔐 Generating secure API key..."
echo ""

# Generate key
API_KEY=$(openssl rand -hex 32)

echo "Your new API key:"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$API_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📋 How to use:"
echo ""
echo "1. Go to Render Dashboard: https://render.com/dashboard"
echo "2. Select your 'laborit-copilot-api' service"
echo "3. Click 'Environment' tab"
echo "4. Set variable:"
echo ""
echo "   Name:  API_KEY"
echo "   Value: $API_KEY"
echo ""
echo "5. Click 'Save changes' and service will auto-redeploy"
echo ""

echo "🧪 Test the key with:"
echo ""
echo "   curl -X GET https://your-app.onrender.com/api/metrics \\"
echo "     -H 'X-API-Key: $API_KEY'"
echo ""

echo "✅ Done! Keep this key secure and share only with authorized clients."
