from django.db import models
from argus.incident.models import Incident

# Create your models here.
class EndpointEvent(models.Model):
    incident = models.ForeignKey(
        to=Incident,
        on_delete=models.CASCADE,
        related_name="endpoint_events",
    )
    name = models.TextField()
    description = models.TextField()

