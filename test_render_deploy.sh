#!/bin/bash
# ============================================================================
# POST-DEPLOYMENT SMOKE TEST SCRIPT FOR RENDER
# ============================================================================
#
# Usage:
#   chmod +x test_render_deploy.sh
#   ./test_render_deploy.sh <your-app-url> [api-key]
#
# Example:
#   ./test_render_deploy.sh https://laborit-copilot-api.onrender.com
#   ./test_render_deploy.sh https://laborit-copilot-api.onrender.com my-secret-key
#
# ============================================================================

set -e

APP_URL="${1:?Error: Missing APP_URL. Usage: $0 <url> [api-key]}"
API_KEY="${2:-}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# Helper functions
# ============================================================================

test_endpoint() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    local data="$5"
    
    echo ""
    echo -e "${BLUE}Testing:${NC} $test_name"
    
    # Build curl command
    local curl_cmd="curl -s -w '\n%{http_code}' -X $method"
    
    if [ -n "$API_KEY" ]; then
        curl_cmd="$curl_cmd -H 'X-API-Key: $API_KEY'"
    fi
    
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$APP_URL$endpoint'"
    
    # Execute and capture response
    local response=$(eval $curl_cmd)
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    echo "  Method: $method"
    echo "  Endpoint: $endpoint"
    echo "  Expected Status: $expected_status"
    echo "  Actual Status: $http_code"
    
    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        ((TESTS_PASSED++))
        
        # Show response body if JSON
        if [ -n "$body" ] && echo "$body" | grep -q "{"; then
            echo "  Response (first 200 chars):"
            echo "$body" | head -c 200
            echo ""
        fi
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        ((TESTS_FAILED++))
        echo "  Response body:"
        echo "$body" | head -c 300
        echo ""
    fi
}

# ============================================================================
# Main tests
# ============================================================================

echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  RENDER DEPLOYMENT SMOKE TEST                                 ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  App URL: $APP_URL"
echo "  API Key: ${API_KEY:-(not set)}"

echo ""
echo -e "${YELLOW}─────────────────────────────────────────────────────────────────${NC}"
echo -e "${YELLOW}1. BASIC CONNECTIVITY TESTS${NC}"
echo -e "${YELLOW}─────────────────────────────────────────────────────────────────${NC}"

test_endpoint "Health check (200)" "GET" "/api/health" 200

test_endpoint "Not found (404)" "GET" "/api/nonexistent" 404

echo ""
echo -e "${YELLOW}─────────────────────────────────────────────────────────────────${NC}"
echo -e "${YELLOW}2. PROTECTED ENDPOINTS TEST${NC}"
echo -e "${YELLOW}─────────────────────────────────────────────────────────────────${NC}"

if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}Skipping protected endpoint tests (no API key provided)${NC}"
    echo "Use: ./test_render_deploy.sh $APP_URL <your-api-key>"
else
    test_endpoint "Metrics endpoint (200)" "GET" "/api/metrics" 200
    
    test_endpoint "Copilot greeting" "POST" "/api/copilot/question" 200 \
        '{"user_input": "Oi, tudo bem?"}'
    
    test_endpoint "Copilot question" "POST" "/api/copilot/question" 200 \
        '{"user_input": "Quantos clientes ativos?"}'
fi

echo ""
echo -e "${YELLOW}─────────────────────────────────────────────────────────────────${NC}"
echo -e "${YELLOW}3. SUMMARY${NC}"
echo -e "${YELLOW}─────────────────────────────────────────────────────────────────${NC}"

TOTAL=$((TESTS_PASSED + TESTS_FAILED))

echo ""
echo "  Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo "  Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo "  Total Tests:  $TOTAL"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC} Deployment is healthy."
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED!${NC} Check the logs above."
    exit 1
fi
