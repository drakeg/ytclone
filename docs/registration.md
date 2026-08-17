# Registration

User registration uses `yt.forms.RegistrationForm`, which extends Django's `UserCreationForm` and explicitly rejects usernames that already exist, including case-only variants. Duplicate submissions return a form validation error instead of reaching the database uniqueness constraint.
