import re

from django.db import transaction

from video.models import VideoChapter


CHAPTER_PATTERN = re.compile(r"^(?P<timestamp>\d{1,3}:\d{2}(?::\d{2})?)\s+(?P<title>.+)$")
MAX_CHAPTERS = 50


class ChapterValidationError(ValueError):
    pass


def parse_chapters(text):
    chapters = []
    for line_number, raw_line in enumerate((text or "").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        match = CHAPTER_PATTERN.fullmatch(line)
        if not match:
            raise ChapterValidationError(f"Line {line_number}: use MM:SS Title or HH:MM:SS Title.")
        parts = [int(part) for part in match.group("timestamp").split(":")]
        if len(parts) == 2:
            minutes, seconds = parts
            start_seconds = minutes * 60 + seconds
        else:
            hours, minutes, seconds = parts
            if minutes >= 60:
                raise ChapterValidationError(f"Line {line_number}: minutes must be below 60 in HH:MM:SS.")
            start_seconds = hours * 3600 + minutes * 60 + seconds
        if seconds >= 60:
            raise ChapterValidationError(f"Line {line_number}: seconds must be below 60.")
        title = match.group("title").strip()
        if len(title) > 120:
            raise ChapterValidationError(f"Line {line_number}: titles must be 120 characters or fewer.")
        chapters.append((start_seconds, title))
    if len(chapters) > MAX_CHAPTERS:
        raise ChapterValidationError("Use no more than 50 chapters.")
    if chapters and chapters[0][0] != 0:
        raise ChapterValidationError("The first chapter must start at 0:00.")
    if any(current[0] <= previous[0] for previous, current in zip(chapters, chapters[1:])):
        raise ChapterValidationError("Chapter timestamps must increase strictly.")
    return chapters


def format_chapters(video):
    lines = []
    for chapter in video.chapters.all():
        hours, remainder = divmod(chapter.start_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        timestamp = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
        lines.append(f"{timestamp} {chapter.title}")
    return "\n".join(lines)


@transaction.atomic
def replace_chapters(video, chapters):
    video.chapters.all().delete()
    VideoChapter.objects.bulk_create(VideoChapter(video=video, start_seconds=start, title=title) for start, title in chapters)
