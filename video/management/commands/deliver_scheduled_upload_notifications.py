from django.core.management.base import BaseCommand, CommandError

from video.services.notifications import deliver_due_scheduled_upload_notifications


class Command(BaseCommand):
    help = "Deliver in-app subscriber notifications for due scheduled video uploads."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of due videos to process (default: 100).",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        if limit < 1 or limit > 1000:
            raise CommandError("--limit must be between 1 and 1000.")
        videos, notifications = deliver_due_scheduled_upload_notifications(limit=limit)
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {videos} due scheduled video(s); created {notifications} subscriber notification(s)."
            )
        )
