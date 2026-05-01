"""
Authentication Serializers for MuseWave API
Handles login, password change, and password reset functionality
"""

from django.db.models import Q
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Login serializer supporting username OR email."""
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )

    def validate(self, attrs):
        username_or_email = attrs.get('username_or_email')
        password          = attrs.get('password')

        if not username_or_email or not password:
            raise serializers.ValidationError(_('Must include username/email and password'))

        user = User.objects.filter(
            Q(username=username_or_email) | Q(email=username_or_email)
        ).first()

        if not user:
            raise serializers.ValidationError(_('Invalid credentials'))

        authenticated_user = authenticate(
            request=self.context.get('request'),
            username=user.get_username(),
            password=password,
        )

        if not authenticated_user:
            raise serializers.ValidationError(_('Invalid credentials'))

        if not authenticated_user.is_active:
            raise serializers.ValidationError(_('User account is disabled'))

        attrs['user'] = authenticated_user
        return attrs


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for user details returned in authentication responses.
    Returns avatar and header URLs directly (same as UserSerializer).
    """
    social_links = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'display_name', 'bio',
            'avatar_url', 'header_url', 'location', 'website',
            'social_links', 'verified', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_social_links(self, obj):
        return {
            'twitter':    obj.twitter,
            'instagram':  obj.instagram,
            'spotify':    obj.spotify,
            'soundcloud': obj.soundcloud,
        }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Current password is incorrect'))
        return value

    def validate(self, attrs):
        new_password         = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')

        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {'new_password_confirm': _('Passwords do not match')}
            )

        user = self.context['request'].user
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})

        if attrs.get('old_password') == new_password:
            raise serializers.ValidationError(
                {'new_password': _('New password must be different from current password')}
            )

        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value, is_active=True)
            self.context['user'] = user
        except User.DoesNotExist:
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid                  = serializers.CharField(required=True)
    token                = serializers.CharField(required=True)
    new_password         = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        try:
            uid  = urlsafe_base64_decode(attrs['uid']).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'uid': _('Invalid reset link')})

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({'token': _('Invalid or expired reset link')})

        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': _('Passwords do not match')})

        try:
            validate_password(attrs['new_password'], user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user