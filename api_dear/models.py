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


class DearCredentials(models.Model):
    dear_url = models.CharField(max_length=200)
    active = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Setting"
        verbose_name_plural = "Settings"

    def __str__(self):
        return self.dear_url


class DearEfrisClientCredentials(ClientCredentials):
    dear_url = models.ForeignKey(DearCredentials, on_delete=models.CASCADE)

    dear_account_id = models.CharField(
        max_length=255,
        default="39efa556-8dda-4c81-83d3-a631e59eb6d3",
    )

    dear_app_key = models.CharField(
        max_length=150,
        default="NONE",
    )

    dear_tax_pin_field = models.CharField(
        max_length=150,
        default="NONE",
    )

    dear_buyer_type_field = models.CharField(
        max_length=150,
        default="NONE",
    )

    dear_is_export_field = models.CharField(
        max_length=150,
        default="NONE",
    )

    dear_default_cashier = models.CharField(
        max_length=150,
        default="NONE",
    )

    dear_stock_description_field = models.CharField(
        max_length=150,
        default="NONE",
    )

    dear_stock_measure_unit_field = models.CharField(
        max_length=150,
        default="NONE",
    )

    dear_stock_commodity_category_field = models.CharField(
        max_length=150,
        default="NONE",
    )

    dear_stock_currency_field = models.CharField(
        max_length=150,
        default="NONE",
    )

    dear_stock_in_price_field = models.CharField(
        max_length=150,
        default="NONE",
    )

    class Meta:
        verbose_name = "Credentials"
        verbose_name_plural = "Credentials"

    def __str__(self):
        return self.company_name


class DearEfrisGoodsConfiguration(EfrisGoodsConfiguration):
    client_account = models.ForeignKey(
        DearEfrisClientCredentials, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Goods Configuration"
        verbose_name_plural = "Goods Configuration"

    def __str__(self):
        return self.goods_name


class DearEfrisGoodsAdjustment(EfrisGoodsAdjustment):
    good = models.ForeignKey(
        DearEfrisGoodsConfiguration, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Goods Adjustment"
        verbose_name_plural = "Goods Adjustment"

    def __str__(self):
        return self.good.goods_name


class DearOutgoingInvoice(EfrisOutgoingInvoice):
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Invoices"
        verbose_name_plural = "Invoices"


@receiver(post_save, sender=DearEfrisGoodsAdjustment)
def create_efris_goods_adjustment(sender, instance, **kwargs):
    from .services import create_xero_goods_adjustment

    create_xero_goods_adjustment(instance.__dict__)


@receiver(post_save, sender=DearEfrisGoodsConfiguration)
def create_efris_goods_configuration(sender, instance, **kwargs):
    from .services import create_xero_goods_configuration

    create_xero_goods_configuration(instance.__dict__)
