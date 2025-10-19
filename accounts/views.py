from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    ResendVerificationEmailSerializer,
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import jwt
from rest_framework_simplejwt.exceptions import TokenError


class MeView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = RefreshToken.for_user(user).access_token

        current_site = get_current_site(request).domain
        relative_link = reverse("verify-email")
        verification_url = f"http://{current_site}{relative_link}?token={str(token)}"

        subject = "Verify your email"
        message = f"Hi {user.username}, please use this link to verify your email: \n{verification_url}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)

        return Response(
            {
                "message": "User created successfully. Please check your email to verify your account."
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(views.APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        token = request.GET.get("token")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])
            if not user.is_active:
                user.is_active = True
                user.save()
            return Response(
                {"message": "Email successfully verified"}, status=status.HTTP_200_OK
            )
        except jwt.ExpiredSignatureError:
            return Response(
                {"error": "Activation link expired"}, status=status.HTTP_400_BAD_REQUEST
            )
        except (jwt.exceptions.DecodeError, TokenError):
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class ResendVerificationEmailView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ResendVerificationEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_active:
            return Response(
                {"message": "This account has already been verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = RefreshToken.for_user(user).access_token

        current_site = get_current_site(request).domain
        relative_link = reverse("verify-email")
        verification_url = f"http://{current_site}{relative_link}?token={str(token)}"

        subject = "Verify your email"
        message = f"Hi {user.username}, please use this link to verify your email: \n{verification_url}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)

        return Response(
            {
                "message": "Verification email has been resent. Please check your email to verify your account."
            },
            status=status.HTTP_200_OK,
        )
