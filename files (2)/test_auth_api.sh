#!/bin/bash
# Authentication API Testing Guide
# Test all authentication endpoints with curl

echo "=================================="
echo "MuseWave Authentication API Tests"
echo "=================================="
echo ""

BASE_URL="http://localhost:5000/api"

# ============================================================================
# 1. CREATE TEST USER (if needed)
# ============================================================================
echo "1. Creating test user..."
curl -X POST "$BASE_URL/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "display_name": "Test User",
    "bio": "Testing authentication"
  }'
echo -e "\n\n"

# ============================================================================
# 2. LOGIN WITH EMAIL
# ============================================================================
echo "2. Login with email..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/users/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "test@example.com",
    "password": "SecurePass123!"
  }')

echo "$LOGIN_RESPONSE" | jq '.'

# Extract tokens
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.token.access')
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.token.refresh')

echo -e "\n"
echo "Access Token: $ACCESS_TOKEN"
echo "Refresh Token: $REFRESH_TOKEN"
echo -e "\n\n"

# ============================================================================
# 3. LOGIN WITH USERNAME
# ============================================================================
echo "3. Login with username..."
curl -X POST "$BASE_URL/users/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "testuser",
    "password": "SecurePass123!"
  }' | jq '.'
echo -e "\n\n"

# ============================================================================
# 4. VERIFY TOKEN
# ============================================================================
echo "4. Verify token..."
curl -X GET "$BASE_URL/users/verify-token/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo -e "\n\n"

# ============================================================================
# 5. REFRESH TOKEN
# ============================================================================
echo "5. Refresh access token..."
REFRESH_RESPONSE=$(curl -s -X POST "$BASE_URL/users/refresh/" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh\": \"$REFRESH_TOKEN\"
  }")

echo "$REFRESH_RESPONSE" | jq '.'

# Extract new tokens
NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.access')
echo -e "\n"
echo "New Access Token: $NEW_ACCESS_TOKEN"
echo -e "\n\n"

# ============================================================================
# 6. CHANGE PASSWORD
# ============================================================================
echo "6. Change password..."
curl -X POST "$BASE_URL/users/password/change/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "SecurePass123!",
    "new_password": "NewSecurePass456!",
    "new_password_confirm": "NewSecurePass456!"
  }' | jq '.'
echo -e "\n\n"

# ============================================================================
# 7. LOGIN WITH NEW PASSWORD
# ============================================================================
echo "7. Login with new password..."
NEW_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/users/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "test@example.com",
    "password": "NewSecurePass456!"
  }')

echo "$NEW_LOGIN_RESPONSE" | jq '.'

NEW_ACCESS_TOKEN=$(echo "$NEW_LOGIN_RESPONSE" | jq -r '.token.access')
NEW_REFRESH_TOKEN=$(echo "$NEW_LOGIN_RESPONSE" | jq -r '.token.refresh')

echo -e "\n\n"

# ============================================================================
# 8. PASSWORD RESET REQUEST
# ============================================================================
echo "8. Request password reset..."
curl -X POST "$BASE_URL/users/password/reset/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com"
  }' | jq '.'
echo -e "\n\n"

# ============================================================================
# 9. PASSWORD RESET CONFIRM (manual - need token from email)
# ============================================================================
echo "9. Password reset confirm (example - need actual uid and token)..."
echo "Check console output or email for reset link"
echo "Example command:"
echo 'curl -X POST "$BASE_URL/users/password/reset/confirm/" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{
    "uid": "MQ",
    "token": "actual-token-from-email",
    "new_password": "ResetPass789!",
    "new_password_confirm": "ResetPass789!"
  }'"'"' | jq '"'"'.'"'"
echo -e "\n\n"

# ============================================================================
# 10. LOGOUT
# ============================================================================
echo "10. Logout..."
curl -X POST "$BASE_URL/users/logout/" \
  -H "Authorization: Bearer $NEW_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh\": \"$NEW_REFRESH_TOKEN\"
  }" | jq '.'
echo -e "\n\n"

# ============================================================================
# 11. TEST RATE LIMITING
# ============================================================================
echo "11. Testing rate limiting (6 failed attempts)..."
for i in {1..6}; do
  echo "Attempt $i..."
  curl -s -X POST "$BASE_URL/users/login/" \
    -H "Content-Type: application/json" \
    -d '{
      "username_or_email": "test@example.com",
      "password": "WrongPassword"
    }' | jq '.error, .attempts_remaining'
  sleep 1
done
echo -e "\n\n"

# ============================================================================
# 12. ERROR CASES
# ============================================================================
echo "12. Testing error cases..."

echo "12a. Login with missing password..."
curl -X POST "$BASE_URL/users/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "test@example.com"
  }' | jq '.'
echo -e "\n"

echo "12b. Login with wrong password..."
curl -X POST "$BASE_URL/users/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "test@example.com",
    "password": "WrongPassword123"
  }' | jq '.'
echo -e "\n"

echo "12c. Login with non-existent user..."
curl -X POST "$BASE_URL/users/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "nonexistent@example.com",
    "password": "SomePassword123"
  }' | jq '.'
echo -e "\n"

echo "12d. Change password with wrong old password..."
curl -X POST "$BASE_URL/users/password/change/" \
  -H "Authorization: Bearer $NEW_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "WrongOldPassword",
    "new_password": "AnotherPass123!",
    "new_password_confirm": "AnotherPass123!"
  }' | jq '.'
echo -e "\n"

echo "12e. Change password with mismatched new passwords..."
curl -X POST "$BASE_URL/users/password/change/" \
  -H "Authorization: Bearer $NEW_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "NewSecurePass456!",
    "new_password": "Password1",
    "new_password_confirm": "Password2"
  }' | jq '.'
echo -e "\n"

echo "12f. Refresh with invalid token..."
curl -X POST "$BASE_URL/users/refresh/" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "invalid.token.here"
  }' | jq '.'
echo -e "\n"

echo "12g. Access protected endpoint without token..."
curl -X GET "$BASE_URL/users/verify-token/" | jq '.'
echo -e "\n"

echo "=================================="
echo "All tests completed!"
echo "=================================="
