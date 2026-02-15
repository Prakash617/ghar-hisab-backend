from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for returning user data (e.g., in /me/ endpoint)"""
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "profile_image",
            "is_verified",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password2 = serializers.CharField(style={"input_type": "password"}, write_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "password2"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate(self, data):
        """Ensure both passwords match"""
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        """Create user but keep them inactive until email verification"""
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()
        return user


class ResendVerificationEmailSerializer(serializers.Serializer):
    """Serializer for resending verification email"""
    email = serializers.EmailField(required=True)
