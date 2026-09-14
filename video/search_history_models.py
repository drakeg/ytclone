from django.conf import settings
from django.db import models


class SearchHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="search_history",
    )
    query = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-searched_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "query"],
                name="unique_search_history_query_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user}: {self.query}"
