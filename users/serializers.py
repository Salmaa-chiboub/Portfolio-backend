import re
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password, get_password_validators
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError, AuthenticationFailed

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
        # Validation de base du mot de passe
        validate_password(value)
        
        # Validation personnalisée supplémentaire
        if len(value) < 10:
            raise ValidationError("Le mot de passe doit contenir au moins 10 caractères.")
        if not re.search(r'[A-Z]', value):
            raise ValidationError("Le mot de passe doit contenir au moins une majuscule.")
        if not re.search(r'[a-z]', value):
            raise ValidationError("Le mot de passe doit contenir au moins une minuscule.")
        if not re.search(r'[0-9]', value):
            raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', value):
            raise ValidationError("Le mot de passe doit contenir au moins un caractère spécial.")
            
        # Vérification des mots de passe courants
        common_passwords = [
            'password', '123456', '123456789', '12345678', '12345',
            '1234567', '1234567890', 'qwerty', 'abc123', 'password1'
        ]
        if value.lower() in common_passwords:
            raise ValidationError("Ce mot de passe est trop courant. Veuillez en choisir un plus complexe.")
            
        return value

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


# ------------------ Forgot Password ------------------ #
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower().strip()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValidationError("Format d'email invalide")
        if not User.objects.filter(email=value).exists():
            # Ne pas révéler que l'email n'existe pas pour des raisons de sécurité
            return value
        return value

    def save(self, request):
        email = self.validated_data['email'].lower().strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Ne pas révéler que l'utilisateur n'existe pas pour des raisons de sécurité
            return {"message": "Si cet email est enregistré, un lien de réinitialisation a été envoyé."}
            
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        base_url = getattr(settings, 'FRONTEND_URL', None) or os.environ.get('FRONTEND_URL')
        if not base_url:
            raise ValidationError("FRONTEND_URL n'est pas configurée")
        base_url = base_url.rstrip('/')
        reset_link = f"{base_url}/reset-password/{uid}/{token}/"

        # Préparation de l'email en HTML
        subject = "Réinitialisation de votre mot de passe"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com')
        
        # Rendu du template HTML
        html_content = render_to_string('emails/password_reset_email.html', {
            'reset_link': reset_link,
            'user': user
        })
        
        # Création de l'email
        msg = EmailMultiAlternatives(
            subject=subject,
            body="Veuillez activer le HTML pour voir ce message.",
            from_email=from_email,
            to=[email],
            reply_to=[from_email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        try:
            msg.send(fail_silently=False)
        except Exception as e:
            # Logger l'erreur dans un environnement de production
            print(f"Erreur d'envoi d'email: {str(e)}")
            raise ValidationError("Une erreur est survenue lors de l'envoi de l'email.")
            
        return {"message": "Si cet email est enregistré, un lien de réinitialisation a été envoyé."}


# ------------------ Set New Password ------------------ #
class SetNewPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        # Validation de base du mot de passe
        validate_password(value)
        
        # Validation personnalisée supplémentaire
        if len(value) < 10:
            raise ValidationError("Le mot de passe doit contenir au moins 10 caractères.")
        if not re.search(r'[A-Z]', value):
            raise ValidationError("Le mot de passe doit contenir au moins une majuscule.")
        if not re.search(r'[a-z]', value):
            raise ValidationError("Le mot de passe doit contenir au moins une minuscule.")
        if not re.search(r'[0-9]', value):
            raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', value):
            raise ValidationError("Le mot de passe doit contenir au moins un caractère spécial.")
            
        # Vérification des mots de passe courants
        common_passwords = [
            'password', '123456', '123456789', '12345678', '12345',
            '1234567', '1234567890', 'qwerty', 'abc123', 'password1'
        ]
        if value.lower() in common_passwords:
            raise ValidationError("Ce mot de passe est trop courant. Veuillez en choisir un plus complexe.")
            
        return value

    def validate(self, attrs):
        uid = attrs.get('uid')
        token = attrs.get('token')
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid UID")

        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError("Invalid or expired token")

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        password = self.validated_data['new_password']
        user = self.validated_data['user']
        user.set_password(password)
        user.save()

        # Envoyer un email de confirmation de réinitialisation au frontend
        base_url = getattr(settings, 'FRONTEND_URL', None) or os.environ.get('FRONTEND_URL')
        if not base_url:
            # Ne pas échouer la réinitialisation si la variable n'est pas configurée, mais logguer
            try:
                print("FRONTEND_URL n'est pas configurée — impossible d'envoyer l'email de confirmation")
            except Exception:
                pass
            return user

        base_url = base_url.rstrip('/')
        login_link = f"{base_url}/login/"

        subject = "Votre mot de passe a été réinitialisé"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com')

        html_content = render_to_string('emails/password_reset_confirmation.html', {
            'login_link': login_link,
            'user': user
        })

        msg = EmailMultiAlternatives(
            subject=subject,
            body="Veuillez activer le HTML pour voir ce message.",
            from_email=from_email,
            to=[user.email],
            reply_to=[from_email]
        )
        msg.attach_alternative(html_content, "text/html")

        try:
            msg.send(fail_silently=False)
        except Exception as e:
            # Log l'erreur mais ne pas bloquer la réinitialisation
            try:
                print(f"Erreur d'envoi d'email de confirmation: {str(e)}")
            except Exception:
                pass

        return user


# ------------------ Login Serializer ------------------ #
class LoginSerializer(serializers.Serializer):
    """Authenticate using email + password and return JWT tokens."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        value = value.lower().strip()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValidationError("Format d'email invalide")
        return value

    def validate(self, attrs):
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password')
        
        # Vérification du format de l'email
        if not email or not password:
            raise AuthenticationFailed('Veuillez fournir un email et un mot de passe')
            
        # Recherche de l'utilisateur
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Pour des raisons de sécurité, on ne précise pas si l'email existe ou non
            raise AuthenticationFailed('Identifiants invalides')

        # Vérification du mot de passe
        if not user.check_password(password):
            # Enregistrement de la tentative échouée (à implémenter si nécessaire)
            raise AuthenticationFailed('Identifiants invalides')

        # Vérification si le compte est actif
        if not user.is_active:
            raise AuthenticationFailed('Ce compte est désactivé. Veuillez contacter le support.')

        # Vérification des privilèges administrateur
        if not user.is_superuser:
            raise AuthenticationFailed("Vous n'avez pas les droits d'administration nécessaires")

        # Génération des tokens JWT
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
        except Exception as e:
            # En cas d'erreur lors de la génération du token
            raise AuthenticationFailed('Une erreur est survenue lors de la connexion. Veuillez réessayer.')
