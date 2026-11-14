from pathlib import Path

from django.test import SimpleTestCase


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class LocalDockerRuntimeTests(SimpleTestCase):
    def test_dockerfile_prepares_named_volume_mountpoints_for_unprivileged_user(self):
        dockerfile = (REPOSITORY_ROOT / "Dockerfile").read_text()

        directory_setup = "mkdir -p /app/data /app/media /app/staticfiles"
        self.assertIn(directory_setup, dockerfile)
        self.assertIn("chown -R app:app /app", dockerfile)
        self.assertLess(dockerfile.index(directory_setup), dockerfile.index("USER app"))

    def test_compose_allows_web_host_and_csrf_settings_from_environment(self):
        compose = (REPOSITORY_ROOT / "compose.yaml").read_text()

        self.assertIn(
            'DJANGO_ALLOWED_HOSTS: "${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1,web}"',
            compose,
        )
        self.assertIn(
            'DJANGO_CSRF_TRUSTED_ORIGINS: "${DJANGO_CSRF_TRUSTED_ORIGINS:-http://localhost:${APP_PORT:-8000}}"',
            compose,
        )
        self.assertIn('APP_PORT: "${APP_PORT:-8000}"', compose)

    def test_environment_example_keeps_bounded_local_defaults(self):
        environment = (REPOSITORY_ROOT / ".env.example").read_text()

        self.assertIn(
            "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,web",
            environment,
        )
        self.assertIn(
            "DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000",
            environment,
        )
        self.assertNotIn("DJANGO_ALLOWED_HOSTS=*", environment)

    def test_readme_documents_lan_access_without_wildcard_hosts(self):
        readme = (REPOSITORY_ROOT / "README.md").read_text()

        self.assertIn("Access from another device on your local network", readme)
        self.assertIn("DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,web,192.168.0.155", readme)
        self.assertIn("DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8010", readme)
        self.assertIn("Do not use `DJANGO_ALLOWED_HOSTS=*`", readme)

    def test_readme_runtime_baseline_matches_current_dependencies(self):
        readme = (REPOSITORY_ROOT / "README.md").read_text()

        self.assertIn("- Django 6.1.3", readme)
        self.assertIn("- Stripe 17.0.0", readme)
        self.assertIn("- Terraform 1.17.2 for infrastructure validation", readme)
