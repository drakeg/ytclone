# Security

This project treats every state-changing request as an authenticated POST request protected by Django's CSRF middleware.

## Current guarantees

- Anonymous users may browse public videos, channels, categories, and profiles.
- Uploading videos requires authentication.
- Creating comments requires authentication.
- Likes, dislikes, and subscriptions require authentication and POST.
- Users may edit only their own profile.
- Missing resources return HTTP 404 responses.

Additional ownership rules for video and comment editing or deletion will be documented when those features are introduced.
