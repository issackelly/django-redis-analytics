from django.db import models

class Track(models.Model):
    name = models.CharField(max_length=1, help_text="THIS SHOULD NOT BE USED")