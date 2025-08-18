import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from payees.constants import TDS_LEGAL_NAME_CHOICES
from .constants import OPERATION_CHOICES


# Create your models here.
class TDS(models.Model):
    """ Model containing Tax Deducted at Source information """

    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    tds_legal_name = models.CharField(max_length=50,
                                      choices=TDS_LEGAL_NAME_CHOICES,
                                      unique=True)
    tds_percentage = models.FloatField()

    class Meta:
        verbose_name = _("Tax Deducted at Source")
        verbose_name_plural = _("Tax Deducted at Source")

    def __str__(self):
        return self.tds_legal_name


class Component(models.Model):
    """
    Model contains Components name and it's corresponding operations
    """
    component_name = models.CharField(max_length=100)
    operation = models.CharField(max_length=10,
                                 choices=OPERATION_CHOICES)  # 'sum' or 'subtract'

    def __str__(self):
        return self.component_name
