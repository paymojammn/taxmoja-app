from django.db import models

from django.db import models
from jsonfield import JSONField
from oauth2.models import OAuth2ClientCredentials

from manager_efris.models import (
    ClientCredentials,
    EfrisGoodsAdjustment,
    EfrisGoodsConfiguration,
    EfrisOutgoingInvoice,
)

from django.dispatch import receiver
from django.db.models.signals import post_save


class OEEfrisClientCredentials(ClientCredentials):
    oe_url = models.CharField(max_length=200)
    oe_api_key = models.CharField(
        max_length=500,
    )
    stock_configuration_measure_unit = models.CharField(
        max_length=200, null=True, blank=True)
    stock_configuration_currency = models.CharField(
        max_length=200, null=True, blank=True)
    stock_configuration_unit_price = models.CharField(
        max_length=200, null=True, blank=True)
    stock_configuration_commodity_category = models.CharField(
        max_length=200, null=True, blank=True)

    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Credentials"
        verbose_name_plural = "Credentials"

    def __str__(self):
        return self.company_name


class OEEfrisGoodsConfiguration(EfrisGoodsConfiguration):
    client_account = models.ForeignKey(
        OEEfrisClientCredentials, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Goods Configuration"
        verbose_name_plural = "Goods Configuration"

    def __str__(self):
        return self.goods_name


class OEEfrisGoodsAdjustment(EfrisGoodsAdjustment):
    good = models.ForeignKey(
        OEEfrisClientCredentials, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Goods Adjustment"
        verbose_name_plural = "Goods Adjustment"

    def __str__(self):
        return self.good.goods_name


class OEOutgoingInvoice(EfrisOutgoingInvoice):
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"


@receiver(post_save, sender=OEEfrisGoodsAdjustment)
def create_efris_goods_adjustment(sender, instance, **kwargs):
    from .efris import create_xero_goods_adjustment

    # create_xero_goods_adjustment(instance.__dict__)


@receiver(post_save, sender=OEEfrisGoodsConfiguration)
def create_efris_goods_configuration(sender, instance, **kwargs):
    from .efris import create_xero_goods_configuration

    # create_xero_goods_configuration(instance.__dict__)
