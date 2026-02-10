"""
Authentication Views for MuseWave API
Handles login, logout, token management, and password operations
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import logging

from .auth_serializers import (
    LoginSerializer,
    UserDetailSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_tokens_for_user(user):
    """
    Generate JWT tokens for a user
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def check_rate_limit(identifier, max_attempts=5, window_minutes=15):
    """
    Check if an identifier has exceeded rate limit
    Returns (is_limited, attempts_remaining)
    """
    cache_key = f'auth_attempts_{identifier}'
    attempts = cache.get(cache_key, 0)
    
    if attempts >= max_attempts:
        return True, 0
    
    return False, max_attempts - attempts


def increment_rate_limit(identifier, window_minutes=15):
    """
    Increment rate limit counter for an identifier
    """
    cache_key = f'auth_attempts_{identifier}'
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, window_minutes * 60)


def reset_rate_limit(identifier):
    """
    Reset rate limit counter for an identifier
    """
    cache_key = f'auth_attempts_{identifier}'
    cache.delete(cache_key)


def log_auth_attempt(username_or_email, success, ip_address, user_agent):
    """
    Log authentication attempts for security monitoring
    """
    logger.info(
        f"Auth attempt - User: {username_or_email}, "
        f"Success: {success}, IP: {ip_address}, UA: {user_agent}"
    )


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    User login endpoint
    
    POST /api/users/login/
    
    Request body:
    {
        "username_or_email": "user@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "token": {
            "refresh": "...",
            "access": "..."
        },
        "user": {
            "id": 1,
            "username": "...",
            "email": "..."
        },
        "message": "Login successful"
    }
    """
    # Get client IP and user agent
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    username_or_email = request.data.get('username_or_email', '')
    
    # Check rate limit
    rate_limit_key = f"{ip_address}_{username_or_email}"
    is_limited, attempts_remaining = check_rate_limit(rate_limit_key)
    
    if is_limited:
        log_auth_attempt(username_or_email, False, ip_address, user_agent)
        return Response(
            {
                'error': 'Too many login attempts. Please try again later.',
                'status': 429
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Validate credentials
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Generate tokens
        tokens = get_tokens_for_user(user)
        
        # Reset rate limit on successful login
        reset_rate_limit(rate_limit_key)
        
        # Log successful attempt
        log_auth_attempt(username_or_email, True, ip_address, user_agent)
        
        # Prepare response
        user_serializer = UserDetailSerializer(user)
        
        return Response(
            {
                'token': tokens,
                'user': user_serializer.data,
                'message': 'Login successful'
            },
            status=status.HTTP_200_OK
        )
    
    # Increment rate limit on failed attempt
    increment_rate_limit(rate_limit_key)
    
    # Log failed attempt
    log_auth_attempt(username_or_email, False, ip_address, user_agent)
    
    return Response(
        {
            'error': 'Invalid credentials',
            'status': 401,
            'attempts_remaining': attempts_remaining - 1
        },
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    User logout endpoint
    
    POST /api/users/logout/
    
    Request headers:
    Authorization: Bearer <access_token>
    
    Request body:
    {
        "refresh": "refresh_token_here"
    }
    
    Response:
    {
        "message": "Logout successful"
    }
    """
    try:
        refresh_token = request.data.get('refresh')
        
        if refresh_token:
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )
    
    except (TokenError, InvalidToken) as e:
        return Response(
            {'error': 'Invalid token'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response(
            {'error': 'Logout failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh_view(request):
    """
    Refresh access token
    
    POST /api/users/refresh/
    
    Request body:
    {
        "refresh": "refresh_token_here"
    }
    
    Response:
    {
        "access": "new_access_token",
        "refresh": "new_refresh_token"
    }
    """
    try:
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new tokens
        token = RefreshToken(refresh_token)
        
        return Response(
            {
                'access': str(token.access_token),
                'refresh': str(token)
            },
            status=status.HTTP_200_OK
        )
    
    except (TokenError, InvalidToken) as e:
        return Response(
            {'error': 'Invalid or expired refresh token'},
            status=status.HTTP_401_UNAUTHORIZED
        )


# ============================================================================
# PASSWORD MANAGEMENT ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Change password for authenticated user
    
    POST /api/users/password/change/
    
    Request headers:
    Authorization: Bearer <access_token>
    
    Request body:
    {
        "old_password": "current_password",
        "new_password": "new_password123",
        "new_password_confirm": "new_password123"
    }
    
    Response:
    {
        "message": "Password changed successfully"
    }
    """
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        
        # Log the password change
        logger.info(f"Password changed for user: {request.user.username}")
        
        # Invalidate existing tokens by blacklisting them
        # Note: Client should re-login after password change
        
        return Response(
            {
                'message': 'Password changed successfully. Please login again.',
                'require_reauth': True
            },
            status=status.HTTP_200_OK
        )
    
    return Response(
        {'error': serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """
    Request password reset email
    
    POST /api/users/password/reset/
    
    Request body:
    {
        "email": "user@example.com"
    }
    
    Response:
    {
        "message": "If an account exists with this email, 
                    a password reset link has been sent."
    }
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = serializer.context.get('user')
        
        if user:
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            # In production, use your actual frontend URL
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            # Send email
            try:
                send_mail(
                    subject='Password Reset Request - MuseWave',
                    message=f'''
Hello {user.username},

You requested a password reset for your MuseWave account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
MuseWave Team
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                logger.info(f"Password reset email sent to: {email}")
            
            except Exception as e:
                logger.error(f"Failed to send password reset email: {str(e)}")
        
        # Always return success message for security
        return Response(
            {
                'message': 'If an account exists with this email, '
                          'a password reset link has been sent.'
            },
            status=status.HTTP_200_OK
        )
    
    return Response(
        {'error': serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """
    Confirm password reset with token
    
    POST /api/users/password/reset/confirm/
    
    Request body:
    {
        "uid": "encoded_user_id",
        "token": "reset_token",
        "new_password": "new_password123",
        "new_password_confirm": "new_password123"
    }
    
    Response:
    {
        "message": "Password has been reset successfully"
    }
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        logger.info(f"Password reset completed for user: {user.username}")
        
        return Response(
            {
                'message': 'Password has been reset successfully. '
                          'You can now login with your new password.'
            },
            status=status.HTTP_200_OK
        )
    
    return Response(
        {'error': serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token_view(request):
    """
    Verify if token is valid
    
    GET /api/users/verify-token/
    
    Request headers:
    Authorization: Bearer <access_token>
    
    Response:
    {
        "valid": true,
        "user": {
            "id": 1,
            "username": "..."
        }
    }
    """
    user_serializer = UserDetailSerializer(request.user)
    
    return Response(
        {
            'valid': True,
            'user': user_serializer.data
        },
        status=status.HTTP_200_OK
    )
