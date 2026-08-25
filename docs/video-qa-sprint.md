# Video Q&A Sprint

## Goal

Make video-page conversations easier to navigate by letting viewers explicitly ask questions and letting creators highlight useful answers, while preserving the existing free comment experience.

## Scope

- Add an optional Question flag to top-level video comments.
- Keep ordinary comments as the default so existing clients/forms remain compatible.
- Let the video owner highlight one reply on a question as the creator answer.
- Add a Questions filter on the video page so viewers can jump directly to Q&A.
- Show a small paid-member cue on questions only when the member has already opted into supporter recognition; do not expose membership status otherwise.
- Keep all questions free to ask and read; paid membership is not required for Q&A.
- Reuse existing comment/reply notification and moderation behavior.

## Acceptance criteria

- Existing ordinary comment creation remains unchanged when the Question flag is omitted.
- Only top-level comments can be marked as questions.
- Only the video owner can highlight/unhighlight a direct visible reply as the answer to a question.
- Highlighting a reply on one question does not affect other questions.
- Hidden/deleted replies cannot be newly highlighted and deleting a highlighted reply clears the answer safely.
- The Questions filter shows only visible top-level questions and their visible replies.
- Member-priority presentation never changes authorization or hides free questions.
- Supporter status is shown only when the commenter has an active paid membership for the video's channel and has explicitly opted into the existing supporter badge.
- No external service, paid infrastructure, AWS resource, or Terraform change is introduced.

## Out of scope

- Paid-only Q&A
- Creator response SLAs
- Voting/ranking questions
- AI-generated answers
- Live chat or livestream Q&A
- Email/push notifications

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test video.test_video_qa
python manage.py test
docker compose run --build --rm test
```
