from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class RegistrationTests(TestCase):
    def test_registration_page_is_available(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create an account")

    def test_user_can_register(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password1": "StrongTestPassword123!",
                "password2": "StrongTestPassword123!",
            },
        )

        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(username="existing", password="password123")

        response = self.client.post(
            reverse("register"),
            {
                "username": "existing",
                "password1": "StrongTestPassword123!",
                "password2": "StrongTestPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A user with that username already exists.")
        self.assertEqual(User.objects.filter(username="existing").count(), 1)

    def test_duplicate_username_is_rejected_case_insensitively(self):
        User.objects.create_user(username="Existing", password="password123")

        response = self.client.post(
            reverse("register"),
            {
                "username": "existing",
                "password1": "StrongTestPassword123!",
                "password2": "StrongTestPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A user with that username already exists.")
        self.assertEqual(User.objects.filter(username__iexact="existing").count(), 1)

    def test_password_mismatch_is_rejected(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password1": "StrongTestPassword123!",
                "password2": "DifferentTestPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_login_redirects_to_video_list(self):
        User.objects.create_user(username="viewer", password="StrongTestPassword123!")

        response = self.client.post(
            reverse("login"),
            {
                "username": "viewer",
                "password": "StrongTestPassword123!",
            },
        )

        self.assertRedirects(response, reverse("video_list"))
