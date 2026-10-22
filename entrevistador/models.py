"""Estado privado por navegador, con exclusión de acciones simultáneas."""

from django.contrib.sessions.models import Session
from django.db import models


class Workspace(models.Model):
    owner = models.OneToOneField(Session, on_delete=models.CASCADE, primary_key=True)
    state = models.JSONField(default=dict)
    recording = models.BinaryField(null=True)
    voice = models.BinaryField(null=True)
    busy_until = models.DateTimeField(null=True)
