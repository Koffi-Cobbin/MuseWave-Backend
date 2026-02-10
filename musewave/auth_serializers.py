"""
Authentication Serializers for MuseWave API
Handles login, password change, and password reset functionality
"""

from django.db.models import Q
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from musewave.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode



User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """
    Login serializer supporting username OR email
    """

    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):

        username_or_email = attrs.get("username_or_email")
        password = attrs.get("password")

        if not username_or_email or not password:
            raise serializers.ValidationError(
                _("Must include username/email and password")
            )

        # Single Query to find user by username OR email (case-insensitive)
        user = User.objects.filter(
            Q(username=username_or_email) |
            Q(email=username_or_email)
        ).first()

        if not user:
            raise serializers.ValidationError(_("Invalid credentials"))

        # SAFE AUTHENTICATION (Works With Custom USERNAME_FIELD)
        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=user.get_username(),
            password=password
        )

        if not authenticated_user:
            raise serializers.ValidationError(_("Invalid credentials"))

        # TODO: Implement this when email verification and account activation is added
        # if not authenticated_user.is_active:
        #     raise serializers.ValidationError(_("User account is disabled"))

        attrs["user"] = authenticated_user
        return attrs


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for user details in authentication responses
    """
    social_links = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name', 'bio',
            'avatar_url', 'header_url', 'location', 'website',
            'social_links', 'verified', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_social_links(self, obj):
        return {
            'twitter': obj.twitter,
            'instagram': obj.instagram,
            'spotify': obj.spotify,
            'soundcloud': obj.soundcloud,
        }


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """Validate that old password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _('Current password is incorrect')
            )
        return value
    
    def validate(self, attrs):
        """Validate that new passwords match and meet requirements"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        # Check passwords match
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': _('Passwords do not match')
            })
        
        # Validate password strength
        user = self.context['request'].user
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })
        
        # Check new password is different from old
        if attrs.get('old_password') == new_password:
            raise serializers.ValidationError({
                'new_password': _('New password must be different from current password')
            })
        
        return attrs
    
    def save(self):
        """Update user password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Check if user with this email exists"""
        try:
            user = User.objects.get(email=value, is_active=True)
            self.context['user'] = user
        except User.DoesNotExist:
            # Don't reveal if email exists for security
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation
    """
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate token and passwords"""
        # Decode uid
        try:
            uid = urlsafe_base64_decode(attrs['uid']).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({
                'uid': _('Invalid reset link')
            })
        
        # Check token
        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({
                'token': _('Invalid or expired reset link')
            })
        
        # Check passwords match
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': _('Passwords do not match')
            })
        
        # Validate password strength
        try:
            validate_password(attrs['new_password'], user)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })
        
        attrs['user'] = user
        return attrs
    
    def save(self):
        """Reset user password"""
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
