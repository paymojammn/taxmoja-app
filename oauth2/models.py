from os import environ
from django.db import models
from jsonfield import JSONField


class OAuth2ClientCredentials(models.Model):
    client_id = models.CharField(max_length=100)
    client_secret = models.CharField(max_length=100)
    authorisation_id = models.AutoField(
        primary_key=True, help_text='authorisation_id,access_token')
    webhook_key = models.CharField(max_length=100)

    callback_uri = models.CharField(max_length=150)
    cred_state = JSONField(blank=True, null=True
                           )
    environment = models.CharField(max_length=100, blank=True, null=True, default='sandbox', help_text='quickbooks_env'
                                   )
