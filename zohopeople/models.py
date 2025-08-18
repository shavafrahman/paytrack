from django.db import models


# Create your models here.

class ZohoPeopleFormToken(models.Model):
    access_token = models.CharField(max_length=500, null=False, blank=False)
    refresh_token = models.CharField(max_length=500, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
