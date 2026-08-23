from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from posixpath import join as posix_join

from django.utils import timezone

from video.models import Category, Channel, Video


MANAGED_MEDIA_PREFIXES = (
    "videos/files",
    "videos/thumbnails",
    "channels/thumbnails",
    "categories/thumbnails",
)
DEFAULT_MIN_AGE_HOURS = 24


@dataclass
class MediaCleanupReport:
    referenced: list[str] = field(default_factory=list)
    orphaned: list[str] = field(default_factory=list)
    protected_recent: list[str] = field(default_factory=list)
    protected_unknown_age: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


def referenced_media_names() -> set[str]:
    names: set[str] = set()
    field_queries = (
        (Video, "video_file"),
        (Video, "thumbnail"),
        (Channel, "thumbnail"),
        (Category, "thumbnail"),
    )
    for model, field_name in field_queries:
        for name in model.objects.values_list(field_name, flat=True).iterator():
            if name:
                names.add(str(name).lstrip("/"))
    return names


def iter_storage_files(storage, prefix: str):
    normalized_prefix = prefix.strip("/")
    directories, files = storage.listdir(normalized_prefix)
    for filename in files:
        yield posix_join(normalized_prefix, filename)
    for directory in directories:
        child = posix_join(normalized_prefix, directory)
        yield from iter_storage_files(storage, child)


def _safe_modified_time(storage, name: str):
    try:
        modified = storage.get_modified_time(name)
    except (NotImplementedError, OSError):
        return None
    if timezone.is_naive(modified):
        modified = timezone.make_aware(modified, timezone.get_current_timezone())
    return modified


def cleanup_orphaned_media(
    storage,
    *,
    delete: bool = False,
    min_age_hours: int = DEFAULT_MIN_AGE_HOURS,
    now=None,
) -> MediaCleanupReport:
    if min_age_hours < 0:
        raise ValueError("min_age_hours must be zero or greater")

    current_time = now or timezone.now()
    cutoff = current_time - timedelta(hours=min_age_hours)
    references = referenced_media_names()
    report = MediaCleanupReport()
    seen: set[str] = set()

    for prefix in MANAGED_MEDIA_PREFIXES:
        try:
            stored_names = iter_storage_files(storage, prefix)
            for raw_name in stored_names:
                name = raw_name.lstrip("/")
                if name in seen:
                    continue
                seen.add(name)
                if name in references:
                    report.referenced.append(name)
                    continue

                modified = _safe_modified_time(storage, name)
                if modified is None:
                    report.protected_unknown_age.append(name)
                    continue
                if modified > cutoff:
                    report.protected_recent.append(name)
                    continue

                report.orphaned.append(name)
                if not delete:
                    continue
                try:
                    storage.delete(name)
                except Exception as exc:  # Storage backends expose provider-specific errors.
                    report.failed.append((name, str(exc)))
                else:
                    report.deleted.append(name)
        except FileNotFoundError:
            continue

    for values in (
        report.referenced,
        report.orphaned,
        report.protected_recent,
        report.protected_unknown_age,
        report.deleted,
    ):
        values.sort()
    report.failed.sort(key=lambda item: item[0])
    return report
