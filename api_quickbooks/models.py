from django.db import models
from oauth2.models import OAuth2ClientCredentials

from manager_efris.models import ClientCredentials


class QuickbooksEfrisClientCredentials(ClientCredentials, OAuth2ClientCredentials):
    quick_books_id = models.AutoField(
        primary_key=True, help_text="quickbooks api auto id"
    )
    access_token = models.CharField(
        max_length=1000, blank=True, null=True, default="NONE"
    )
    sandbox_url = models.CharField(
        max_length=1000, blank=True, null=True, default="NONE"
    )
    prod_url = models.CharField(
        max_length=1000, blank=True, null=True, default="NONE")
    refresh_token = models.CharField(
        max_length=1000, blank=True, null=True, default="NONE"
    )
    realm_id = models.CharField(
        max_length=1000, blank=True, null=True, default="NONE")
    auth_code = models.CharField(
        max_length=1000, blank=True, null=True, default="NONE")
    state = models.CharField(
        max_length=1000, blank=True, null=True, default="NONE")
    basic_token = models.CharField(
        max_length=1000, blank=True, null=True, default="NONE"
    )
    refresh_token_expiry = models.CharField(
        max_length=10, blank=True, null=True, default="NONE"
    )
    cashier = models.CharField(
        max_length=100, blank=True, null=True, default="SYSTEM"
    )
    stock_configuration_measure_unit = models.CharField(
        max_length=200, null=True, blank=True)
    stock_configuration_currency = models.CharField(
        max_length=200, null=True, blank=True)
    stock_configuration_unit_price = models.CharField(
        max_length=200, null=True, blank=True)
    stock_configuration_commodity_category = models.CharField(
        max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = "Credentials"
        verbose_name_plural = "Credentials"

    def __str__(self):
        return self.company_name


class Bearer:
    def __init__(
        self,
        refreshExpiry,
        accessToken,
        tokenType,
        refreshToken,
        accessTokenExpiry,
        idToken=None,
    ):
        self.refreshExpiry = refreshExpiry
        self.accessToken = accessToken
        self.tokenType = tokenType
        self.refreshToken = refreshToken
        self.accessTokenExpiry = accessTokenExpiry
        self.idToken = idToken
