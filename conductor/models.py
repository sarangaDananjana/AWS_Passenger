from django.db import models


class ConAppVersion(models.Model):
    version = models.CharField(max_length=10, unique=True)
    update_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.version}"
