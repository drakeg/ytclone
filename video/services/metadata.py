import re

from django.db import transaction

from ..metadata_models import Hashtag, Tag


HASHTAG_PATTERN = re.compile(r"(?<!\w)#([\w]+)", re.UNICODE)
MAX_TAGS = 20
MAX_TAG_LENGTH = 50
MAX_HASHTAGS = 30


def normalize_tag_names(raw: str) -> list[str]:
    seen = set()
    normalized = []
    for item in (raw or "").split(","):
        name = " ".join(item.strip().split()).lower()
        if not name or name in seen:
            continue
        if len(name) > MAX_TAG_LENGTH:
            raise ValueError(f"Tags must be {MAX_TAG_LENGTH} characters or fewer.")
        seen.add(name)
        normalized.append(name)
        if len(normalized) > MAX_TAGS:
            raise ValueError(f"Use no more than {MAX_TAGS} tags.")
    return normalized


def extract_hashtags(*texts: str) -> list[str]:
    seen = set()
    results = []
    for text in texts:
        for match in HASHTAG_PATTERN.finditer(text or ""):
            name = match.group(1).lower()
            if name in seen:
                continue
            seen.add(name)
            results.append(name[:64])
            if len(results) >= MAX_HASHTAGS:
                return results
    return results


@transaction.atomic
def sync_video_metadata(video, structured_tags=None):
    if structured_tags is not None:
        tags = [Tag.objects.get_or_create(name=name)[0] for name in structured_tags]
        video.tags.set(tags)

    hashtag_names = extract_hashtags(video.title, video.description)
    hashtags = [Hashtag.objects.get_or_create(name=name)[0] for name in hashtag_names]
    video.hashtags.set(hashtags)
