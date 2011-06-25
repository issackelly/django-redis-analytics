from django.db import models

class Track(models.Model):
    # There is a better way to do this, just not implemented yet
    name = models.CharField(max_length=1, help_text="THIS SHOULD NOT BE USED")