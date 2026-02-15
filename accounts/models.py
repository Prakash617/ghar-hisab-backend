from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # Use email as the unique identifier for authentication
    username = None  # 🔥 VERY IMPORTANT — remove username field

    email = models.EmailField(unique=True, max_length=254)
    profile_image = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class EmailSettings(SingletonModel):
    EMAIL_BACKEND = models.CharField(
        max_length=255, default="django.core.mail.backends.smtp.EmailBackend"
    )
    EMAIL_HOST = models.CharField(max_length=255, default="smtp.gmail.com")
    EMAIL_PORT = models.PositiveIntegerField(default=587)
    EMAIL_USE_TLS = models.BooleanField(default=True)
    EMAIL_HOST_USER = models.EmailField(blank=True)
    EMAIL_HOST_PASSWORD = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return "Email Settings"
