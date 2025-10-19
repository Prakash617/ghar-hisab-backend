from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.core import mail


class AccountTests(APITestCase):

    def test_register_user(self):
        """
        Ensure we can create a new user.
        """
        url = reverse("register")
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
            "password2": "testpassword",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, "testuser")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Verify your email")

    def test_register_user_with_existing_email(self):
        """
        Ensure we cannot create a new user with an existing email.
        """
        User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        url = reverse("register")
        data = {
            "username": "testuser2",
            "email": "test@example.com",
            "password": "testpassword",
            "password2": "testpassword",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_verification_email(self):
        """
        Ensure we can resend a verification email.
        """
        User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            is_active=False,
        )
        url = reverse("resend-verification-email")
        data = {"email": "test@example.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Verify your email")

    def test_resend_verification_email_with_invalid_email(self):
        """
        Ensure we cannot resend a verification email with an invalid email.
        """
        url = reverse("resend-verification-email")
        data = {"email": "test@example.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_verification_email_for_active_user(self):
        """
        Ensure we cannot resend a verification email for an already active user.
        """
        User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            is_active=True,
        )
        url = reverse("resend-verification-email")
        data = {"email": "test@example.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(mail.outbox), 0)
