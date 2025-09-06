import re
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .utils import (
    send_password_reset_email,
    send_password_reset_confirmation_email,
    validate_strong_password,  # nouvelle fonction utilitaire
)

User = get_user_model()


# ------------------ User Serializer ------------------ #
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']


# ------------------ Change Password ------------------ #
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        return validate_strong_password(value)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Ancien mot de passe incorrect"))
        return value


# ------------------ Forgot Password ------------------ #
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("Aucun utilisateur trouvé avec cet email"))
        return value

    def save(self, **kwargs):
        request = self.context.get('request')
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)

        base_url = settings.FRONTEND_URL
        reset_link = f"{base_url}/reset-password/{uid}/{token}/"

        send_password_reset_email(user, reset_link)


# ------------------ Reset Password (fusionné) ------------------ #
class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        return validate_strong_password(value)

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(_("Lien de réinitialisation invalide."))

        if not PasswordResetTokenGenerator().check_token(user, attrs['token']):
            raise serializers.ValidationError(_("Lien de réinitialisation invalide ou expiré."))

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        request = self.context.get('request')
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']

        user.set_password(new_password)
        user.save()

        base_url = settings.FRONTEND_URL
        login_link = f"{base_url}/login/"

        send_password_reset_confirmation_email(user, login_link)
        return user


# ------------------ Login Serializer ------------------ #
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        value = value.lower().strip()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValidationError(_("Format d'email invalide"))
        return value

    def validate(self, attrs):
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password')

        if not email or not password:
            raise AuthenticationFailed(_("Veuillez fournir un email et un mot de passe"))

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed(_("Identifiants invalides"))

        if not user.check_password(password):
            raise AuthenticationFailed(_("Identifiants invalides"))

        if not user.is_active:
            raise AuthenticationFailed(_("Ce compte est désactivé. Veuillez contacter le support."))

        if not user.is_superuser:
            raise AuthenticationFailed(_("Vous n'avez pas les droits d'administration nécessaires"))

        try:
            refresh = RefreshToken.for_user(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_superuser': user.is_superuser
                }
            }
        except Exception:
            raise AuthenticationFailed(_("Une erreur est survenue lors de la connexion. Veuillez réessayer."))
