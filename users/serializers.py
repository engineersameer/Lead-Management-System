from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer
from django.contrib.auth import authenticate
from .models import User

# In case User Forget it's password, we can use this serializer to reset the password using the token sent to the user's email.
from django.contrib.auth.tokens import default_token_generator

from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )

        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")

        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        # Implementing the authentication logic using Django's built-in authenticate function
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )

        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        # If user is not active, raise a validation error
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")

        attrs["user"] = user

        return attrs


class LogoutSerializer(TokenBlacklistSerializer):
    pass


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")

        return value

    def validate_new_password(self, value):
        user = self.context["request"].user

        if user.check_password(value):
            raise serializers.ValidationError(
                "New password must be different from the old password."
            )

        validate_password(value, user=user)

        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = User.objects.filter(
            email=value,
            is_active=True,
        ).first()

        if not user:
            raise serializers.ValidationError("No active user found with this email.")

        self.user = user
        return value

    def create(self, validated_data):
        user = self.user
        token = default_token_generator.make_token(user)

        return {
            "user_id": user.id,
            "token": token,
        }


class ResetPasswordSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user = User.objects.get(
                id=attrs["user_id"],
                is_active=True,
            )
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": "Invalid user."})

        if not default_token_generator.check_token(
            user,
            attrs["token"],
        ):
            raise serializers.ValidationError(
                {"token": "Invalid or expired reset token."}
            )

        validate_password(
            attrs["new_password"],
            user=user,
        )

        attrs["user"] = user

        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()

        return user
