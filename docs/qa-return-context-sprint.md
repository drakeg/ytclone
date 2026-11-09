# Q&A Return Context Sprint

## Goal

Preserve the viewer's current comment location after Q&A mutations so asking a question or highlighting/unhighlighting an answer does not drop the user back to the base video page.

## Scope

- Reuse the existing same-host `safe_return_url` helper.
- Preserve the current paginated/filter/sort video-detail URL after asking a question.
- Preserve the current video-detail or full-thread URL after highlighting or unhighlighting a question answer.
- Carry `next` through the existing Q&A forms.
- Keep canonical video-detail fallbacks for missing or unsafe targets.
- Keep existing Q&A authorization, visibility, and featured-answer behavior unchanged.

## Acceptance criteria

1. Asking a question returns to the originating video-detail page/filter/sort context.
2. Highlighting or unhighlighting an answer returns to the originating detail or full-thread view.
3. Unsafe external `next` targets are rejected.
4. Missing `next` falls back to the canonical video detail.
5. Unlisted/shared comment routes continue to work only within existing visibility/share-token rules.
6. No schema, migration, dependency, worker, queue, AWS resource, paid service, or live-payment change is introduced.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_qa video.test_qa_return_context video.test_comment_return_context
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- New Q&A features
- Arbitrary nested replies
- Notifications changes
- Comment ranking
- AJAX/infinite scrolling
