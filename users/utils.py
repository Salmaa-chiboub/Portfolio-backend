import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
import re
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

logger = logging.getLogger(__name__)



def validate_strong_password(value):
    """Validation avancée de mot de passe (longueur, majuscules, chiffres, etc.)."""
    validate_password(value)

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

    common_passwords = [
        'password', '123456', '123456789', '12345678', '12345',
        '1234567', '1234567890', 'qwerty', 'abc123', 'password1'
    ]
    if value.lower() in common_passwords:
        raise ValidationError("Ce mot de passe est trop courant. Veuillez en choisir un plus complexe.")

    return value


def send_email(subject, template, context, recipients, fail_silently=False):
    """Envoi générique d'un email HTML + texte brut."""
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com')

    try:
        html_content = render_to_string(template, context)
    except Exception as e:
        logger.error(f"Erreur rendu template {template}: {e}")
        raise

    msg = EmailMultiAlternatives(
        subject=subject,
        body=_("Veuillez activer le HTML pour voir ce message."),
        from_email=from_email,
        to=recipients,
        reply_to=[from_email]
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=fail_silently)
        logger.info(f"Email envoyé à {recipients} (sujet: {subject})")
    except Exception as e:
        logger.error(f"Erreur d'envoi d'email: {e}")
        if not fail_silently:
            raise


# ---- Emails spécifiques ---- #
def send_password_reset_email(user, reset_link):
    """Envoi de l'email de réinitialisation."""
    send_email(
        subject=_("Réinitialisation de votre mot de passe"),
        template="emails/password_reset_email.html",
        context={"reset_link": reset_link, "user": user},
        recipients=[user.email]
    )


def send_password_reset_confirmation_email(user, login_link):
    """Envoi de la confirmation après réinitialisation."""
    send_email(
        subject=_("Votre mot de passe a été réinitialisé"),
        template="emails/password_reset_confirmation.html",
        context={"login_link": login_link, "user": user},
        recipients=[user.email]
    )
