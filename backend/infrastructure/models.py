"""Persistence models (infrastructure concern).

This Django ORM model stores a planned trip so the UI can show history. The
domain layer never imports it — the repository maps between the two.
"""

from django.db import models


class Trip(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    current_location = models.CharField(max_length=500)
    pickup_location = models.CharField(max_length=500)
    dropoff_location = models.CharField(max_length=500)
    current_cycle_used_hours = models.FloatField()

    total_miles = models.FloatField(default=0)
    total_drive_hours = models.FloatField(default=0)
    days = models.PositiveIntegerField(default=0)

    request_payload = models.JSONField()
    result = models.JSONField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.pickup_location} -> {self.dropoff_location} ({self.created_at:%Y-%m-%d})"
