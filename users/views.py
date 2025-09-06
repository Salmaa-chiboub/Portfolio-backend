from django.contrib.auth import get_user_model
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import (
    UserSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    LoginSerializer,
)

from core.permissions import IsSuperUser

User = get_user_model()


# ------------------ Profile ------------------ #
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# ------------------ Change Password ------------------ #
class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_password = serializer.validated_data['old_password']
        if not user.check_password(old_password):
            return Response(
                {'old_password': ['Mot de passe actuel incorrect.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Mot de passe mis à jour avec succès.'})


# ------------------ Login ------------------ #
class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


# ------------------ Forgot Password ------------------ #
class ForgotPasswordView(generics.GenericAPIView):
    """
    Endpoint public pour demander un lien de réinitialisation de mot de passe.
    """
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Si l'email est enregistré, un lien de réinitialisation a été envoyé."},
            status=status.HTTP_200_OK
        )


# ------------------ Admin-only: Request Password Reset ------------------ #
class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [IsSuperUser]  # réservé aux superusers

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Lien de réinitialisation envoyé (si l'email existe)."},
            status=status.HTTP_200_OK
        )


# ------------------ Reset Password ------------------ #
class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]  # ou [IsSuperUser] si tu veux restreindre

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Mot de passe réinitialisé avec succès.'}, status=status.HTTP_200_OK)
