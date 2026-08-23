from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from video.services.media_cleanup import DEFAULT_MIN_AGE_HOURS, cleanup_orphaned_media


class Command(BaseCommand):
    help = "Report or delete orphaned application media from the configured storage backend."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete eligible orphaned objects. Without this flag the command is a dry run.",
        )
        parser.add_argument(
            "--min-age-hours",
            type=int,
            default=DEFAULT_MIN_AGE_HOURS,
            help=(
                "Protect orphaned objects newer than this many hours from deletion "
                f"(default: {DEFAULT_MIN_AGE_HOURS})."
            ),
        )

    def handle(self, *args, **options):
        delete = options["delete"]
        min_age_hours = options["min_age_hours"]
        if min_age_hours < 0:
            raise CommandError("--min-age-hours must be zero or greater")

        report = cleanup_orphaned_media(
            default_storage,
            delete=delete,
            min_age_hours=min_age_hours,
        )

        mode = "DELETE" if delete else "DRY RUN"
        self.stdout.write(f"Media cleanup mode: {mode}")
        self.stdout.write(f"Minimum orphan age: {min_age_hours} hour(s)")
        self.stdout.write(f"Referenced objects found: {len(report.referenced)}")
        self.stdout.write(f"Eligible orphaned objects: {len(report.orphaned)}")
        self.stdout.write(f"Protected recent orphans: {len(report.protected_recent)}")
        self.stdout.write(
            f"Protected orphans with unknown age: {len(report.protected_unknown_age)}"
        )

        if report.orphaned:
            self.stdout.write("Eligible orphans:")
            for name in report.orphaned:
                action = "deleted" if name in report.deleted else "would delete"
                if delete and name not in report.deleted:
                    action = "delete failed"
                self.stdout.write(f"  {name} [{action}]")

        if report.protected_recent:
            self.stdout.write("Recent orphans left untouched:")
            for name in report.protected_recent:
                self.stdout.write(f"  {name}")

        if report.protected_unknown_age:
            self.stdout.write("Unknown-age orphans left untouched:")
            for name in report.protected_unknown_age:
                self.stdout.write(f"  {name}")

        if report.failed:
            self.stderr.write("Deletion failures:")
            for name, error in report.failed:
                self.stderr.write(f"  {name}: {error}")
            raise CommandError(f"Failed to delete {len(report.failed)} media object(s).")

        if delete:
            self.stdout.write(self.style.SUCCESS(f"Deleted {len(report.deleted)} orphaned object(s)."))
        else:
            self.stdout.write("Dry run complete; no media objects were deleted.")
