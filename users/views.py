from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny


from .serializers import (
	UserSerializer,
	ChangePasswordSerializer,
	ForgotPasswordSerializer, 
	SetNewPasswordSerializer,
	LoginSerializer,
)

User = get_user_model()


from core.permissions import IsSuperUser


# Registration endpoint removed. Superusers should create users via admin React or manage.py createsuperuser.


class ProfileView(generics.RetrieveUpdateAPIView):
	serializer_class = UserSerializer
	permission_classes = [IsAuthenticated]

	def get_object(self):
		return self.request.user


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
			return Response({'old_password': ['Wrong password.']}, status=status.HTTP_400_BAD_REQUEST)
		user.set_password(serializer.validated_data['new_password'])
		user.save()
		return Response({'detail': 'Password updated successfully.'})


class LoginView(generics.GenericAPIView):
	permission_classes = [permissions.AllowAny]
	serializer_class = LoginSerializer

	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		return Response(serializer.validated_data)
	

class ForgotPasswordView(generics.GenericAPIView):
    """
    Endpoint pour demander un lien de réinitialisation de mot de passe.
    Accessible à tous les utilisateurs (AllowAny), mais dans ton projet tu peux
    restreindre aux superusers si nécessaire.
    """
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request=request)  # Le serializer envoie l'email
        return Response(
            {"detail": "Si l'email est enregistré, un lien de réinitialisation a été envoyé."},
            status=status.HTTP_200_OK
        )

class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [IsSuperUser]  # ou AllowAny selon ton besoin

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request=request)
        return Response(
            {"detail": "Si l'email est enregistré, un lien de réinitialisation a été envoyé."},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [IsSuperUser]  # ou AllowAny

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)
