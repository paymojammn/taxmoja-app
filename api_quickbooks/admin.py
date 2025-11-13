# admin.py
from django.contrib import admin
from django import forms
from django.forms import PasswordInput
from unfold.admin import ModelAdmin

from .models import QuickbooksEfrisClientCredentials

# --- Optional quick branding (you can also use UNFOLD settings in settings.py) ---
admin.site.site_header = "Centry"
admin.site.site_title = "Centry Admin"
admin.site.index_title = "Welcome to Centry"


class QuickbooksCredentialsForm(forms.ModelForm):
    class Meta:
        model = QuickbooksEfrisClientCredentials
        fields = "__all__"
        widgets = {
            # Mask secrets / tokens in the admin form
            "access_token": PasswordInput(render_value=True),
            "refresh_token": PasswordInput(render_value=True),
            "basic_token": PasswordInput(render_value=True),
            "auth_code": PasswordInput(render_value=True),
            "state": PasswordInput(render_value=True),
        }


@admin.register(QuickbooksEfrisClientCredentials)
class QuickbooksEfrisClientCredentialsAdmin(ModelAdmin):
    form = QuickbooksCredentialsForm

    # Summary list
    list_display = (
        "quick_books_id",
        "company_name",
        "realm_id",
        "cashier",
        "short_access_token",
        "short_refresh_token",
    )
    search_fields = ("company_name", "realm_id", "cashier")
    list_filter = ("cashier",)
    ordering = ("company_name",)
    readonly_fields = ("quick_books_id",)  # keep the PK read-only
    list_per_page = 50

    # Group the edit form nicely
    fieldsets = (
        ("Company", {"fields": ("company_name", "cashier")}),
        ("Environment", {"fields": ("sandbox_url", "prod_url")}),
        ("QuickBooks OAuth", {
            "fields": (
                "realm_id",
                "auth_code",
                "state",
                "access_token",
                "refresh_token",
                "basic_token",
                "refresh_token_expiry",
            )
        }),
        ("Default Stock Configuration", {
            "fields": (
                "stock_configuration_measure_unit",
                "stock_configuration_currency",
                "stock_configuration_unit_price",
                "stock_configuration_commodity_category",
            )
        }),
        ("Internal", {"fields": ("quick_books_id",)}),
    )

    # Short, safe token previews in list display
    def _short(self, val: str, length: int = 8):
        if not val or val == "NONE":
            return "—"
        return f"{val[:length]}…"

    def short_access_token(self, obj):
        return self._short(obj.access_token)
    short_access_token.short_description = "Access Token"

    def short_refresh_token(self, obj):
        return self._short(obj.refresh_token)
    short_refresh_token.short_description = "Refresh Token"
