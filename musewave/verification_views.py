"""
Email Verification Views for MuseWave API
Handles email verification and sends welcome email with credentials after verification
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from .models import User
import logging

logger = logging.getLogger(__name__)


def send_welcome_email_with_credentials(user, password):
    """Send welcome email with login credentials after successful verification"""
    try:
        subject = 'Welcome to MuseWave - Your Account is Verified!'

        message = f"""
Hello {user.display_name or user.username}!

Congratulations! Your MuseWave account has been successfully verified!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your Login Credentials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Username: {user.username}
Email: {user.email}
Password: {password}

Login URL: {settings.FRONTEND_URL}/login

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT:
• Please keep these credentials safe and secure
• We recommend changing your password after your first login

Best regards,
The MuseWave Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        print(f"✅ Welcome email with credentials sent to {user.email}")
        logger.info(f"Welcome email sent to {user.email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send welcome email to {user.email}: {str(e)}")
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, uidb64, token):
    """
    Verify user email using token.
    GET /api/users/verify-email/<uidb64>/<token>/

    Called by the frontend page after extracting uidb64 and token from the URL.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        print(f"🔍 Decoded UID: {uid} from uidb64: {uidb64}")
        user = User.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {
                'success': False,
                'error': 'Invalid verification link',
                'message': 'The verification link is invalid or malformed.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Already verified
    if user.verified:
        return Response(
            {
                'success': True,
                'message': 'Email already verified. You can log in.',
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'verified': True
                }
            },
            status=status.HTTP_200_OK
        )

    # Validate token
    if not default_token_generator.check_token(user, token):
        return Response(
            {
                'success': False,
                'error': 'Invalid or expired token',
                'message': 'The verification link has expired or is invalid. Please request a new verification email.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Retrieve cached plain-text password (stored for 24 h at registration)
    cache_key = f'user_password_{user.id}'
    password = cache.get(cache_key)

    if not password:
        password = "Please reset your password"
        print(f"⚠️  No cached password found for user {user.id}. User will need to reset password.")

    # Mark verified
    user.verified = True
    user.save(update_fields=['verified'])

    print(f"✅ User verified: {user.username} ({user.email})")
    logger.info(f"User {user.id} ({user.email}) email verified successfully")

    # Send welcome email with credentials
    email_sent = send_welcome_email_with_credentials(user, password)

    response_data = {
        'success': True,
        'message': 'Email verified successfully! Check your email for login credentials.',
        'user': {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'verified': True,
            'display_name': user.display_name,
            'password': password if email_sent else "Password not sent due to email error"
        }
    }

    # Clear cached password
    cache.delete(cache_key)

    if not email_sent:
        response_data['warning'] = (
            'Email verified but welcome email could not be sent. '
            'Please contact support for your credentials.'
        )

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """
    Resend verification email to user.
    POST /api/users/resend-verification/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email')

    if not email:
        return Response(
            {'success': False, 'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)

        if user.verified:
            return Response(
                {'success': False, 'message': 'This account is already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rate limit: 1 resend per 5 minutes per user
        rate_limit_key = f'verification_email_{user.id}'
        if cache.get(rate_limit_key):
            return Response(
                {
                    'success': False,
                    'error': 'Too many requests',
                    'message': 'Please wait a few minutes before requesting another verification email'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # ----------------------------------------------------------------
        # Correctly encode the user PK:
        #   force_bytes(user.pk)         → raw bytes of the UUID string
        #   urlsafe_base64_encode(...)   → URL-safe base64 TEXT string  ✅
        #
        # The old bug used urlsafe_base64_decode() here which returned a
        # bytes object — printing that into an f-string gave b'\xd3W...'
        # ----------------------------------------------------------------
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))  # ✅ always a clean string

        # Link goes to the FRONTEND /verify-email page.
        # The frontend reads uid + token from the URL and calls the backend API.
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"

        subject = 'Verify Your MuseWave Account - New Link'
        message = f"""
Hello {user.display_name or user.username}!

You requested a new verification link for your MuseWave account.

Please click the link below to verify your email address:

{verification_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
The MuseWave Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        cache.set(rate_limit_key, True, 300)  # 5-minute rate limit

        print(f"✅ Verification email resent to {user.email}")
        print(f"🔗 Verification URL: {verification_url}")
        logger.info(f"Verification email resent to {user.email}")

        return Response(
            {
                'success': True,
                'message': 'Verification email sent successfully. Please check your inbox.'
            },
            status=status.HTTP_200_OK
        )

    except User.DoesNotExist:
        # Don't reveal whether the email exists
        return Response(
            {
                'success': True,
                'message': 'If an account with this email exists, a verification email has been sent.'
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(f"❌ Error resending verification email: {str(e)}")
        logger.error(f"Error resending verification email: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'Failed to send verification email',
                'message': 'An error occurred. Please try again later.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def check_verification_status(request):
    """
    Check if a user's email is verified.
    GET /api/users/verification-status/?email=user@example.com
    """
    email = request.GET.get('email')

    if not email:
        return Response(
            {'error': 'Email parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
        return Response(
            {
                'email': user.email,
                'verified': user.verified,
                'username': user.username
            },
            status=status.HTTP_200_OK
        )

    except User.DoesNotExist:
        return Response(
            {
                'email': email,
                'verified': False,
                'message': 'No account found with this email'
            },
            status=status.HTTP_404_NOT_FOUND
        )