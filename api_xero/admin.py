# admin.py
from django.contrib import admin
from django import forms
from django.forms import PasswordInput
from unfold.admin import ModelAdmin

from .models import (
    XeroEfrisClientCredentials,
    XeroEfrisGoodsConfiguration,
    XeroEfrisGoodsAdjustment,
    XeroIncomingInvoice,
)

# --- Optional quick branding (or use UNFOLD settings in settings.py) ---
admin.site.site_header = "Centry"
admin.site.site_title = "Centry Admin"
admin.site.index_title = "Welcome to Centry"


# =========================
# Client Credentials (Xero)
# =========================

class XeroCredentialsForm(forms.ModelForm):
    class Meta:
        model = XeroEfrisClientCredentials
        fields = "__all__"
        widgets = {
            # mask secrets in the form
            "client_secret": PasswordInput(render_value=True),
            "webhook_key": PasswordInput(render_value=True),
        }

@admin.register(XeroEfrisClientCredentials)
class XeroEfrisClientCredentialsAdmin(ModelAdmin):
    form = XeroCredentialsForm

    list_display = (
        "authorisation_id",           # PK from OAuth2ClientCredentials
        "company_name",
        "client_id",
        "environment",
        "xero_purchase_account",
        "xero_standard_tax_rate_code",
        "xero_exempt_tax_rate_code",
        "xero_stock_in_contact_account",
    )
    search_fields = (
        "company_name",
        "client_id",
        "environment",
        "xero_purchase_account",
        "xero_stock_in_contact_account",
        "xero_exempt_tax_rate_code",
        "xero_standard_tax_rate_code",
    )
    list_filter = ("environment", "xero_standard_tax_rate_code", "xero_exempt_tax_rate_code")
    ordering = ("company_name",)
    readonly_fields = ("authorisation_id",)

    fieldsets = (
        ("Company", {"fields": ("company_name",)}),
        ("OAuth2 Credentials", {
            "fields": (
                "client_id",
                "client_secret",
                "authorisation_id",
                "webhook_key",
                "callback_uri",
                "cred_state",
                "environment",
            )
        }),
        ("Xero Accounts", {
            "fields": (
                "xero_purchase_account",
                "xero_stock_in_contact_account",
            )
        }),
        ("Tax Codes", {
            "fields": (
                "xero_standard_tax_rate_code",
                "xero_exempt_tax_rate_code",
            )
        }),
    )


# ======================
# Goods Configuration
# ======================

@admin.register(XeroEfrisGoodsConfiguration)
class XeroEfrisGoodsConfigurationAdmin(ModelAdmin):
    list_display = (
        "pk",                         # safe across models even if 'id' isn't defined explicitly
        "goods_name",
        "goods_code",
        "commodity_tax_category",
        "unit_price",
        "currency",
        "measure_unit",
        "client_account",
    )
    search_fields = ("goods_name", "goods_code", "commodity_tax_category")
    list_filter = ("commodity_tax_category", "currency", "measure_unit", "client_account")
    ordering = ("goods_name",)
    # keep ID editable if needed; if you prefer read-only and you do have an AutoField 'id', add: readonly_fields = ("id",)


# =================
# Goods Adjustment
# =================

@admin.register(XeroEfrisGoodsAdjustment)
class XeroEfrisGoodsAdjustmentAdmin(ModelAdmin):
    list_display = (
        "pk",
        "good",
        "xero_invoice_type",
        "safe_quantity",
        "safe_amount",
    )
    search_fields = ("good__goods_name",)
    list_filter = ("xero_invoice_type",)
    ordering = ("-pk",)

    # Guard access to optional fields that may live on the abstract/base model
    def safe_quantity(self, obj):
        return getattr(obj, "quantity", "—")
    safe_quantity.short_description = "Quantity"

    def safe_amount(self, obj):
        for field in ("amount", "total_amount", "unit_price"):
            if hasattr(obj, field):
                return getattr(obj, field)
        return "—"
    safe_amount.short_description = "Amount"


# ===============
# Incoming Invoice
# ===============

@admin.register(XeroIncomingInvoice)
class XeroIncomingInvoiceAdmin(ModelAdmin):
    list_display = (
        "pk",                        # avoids admin.E108 if no concrete 'id' field exists
        "safe_invoice_number",
        "safe_status",
        "safe_date",
        "safe_total",
    )
    search_fields = ("invoice_number",)
    # Only include this if your base model defines a 'status' field.
    list_filter = ("status",) if hasattr(XeroIncomingInvoice, "status") else ()
    ordering = ("-pk",)

    def safe_invoice_number(self, obj):
        return getattr(obj, "invoice_number", f"Invoice #{obj.pk}")
    safe_invoice_number.short_description = "Invoice #"

    def safe_status(self, obj):
        return getattr(obj, "status", "—")
    safe_status.short_description = "Status"

    def safe_date(self, obj):
        # Try common field names found on invoice-ish models
        for f in ("date", "date_created", "created_at", "issue_date"):
            if hasattr(obj, f):
                return getattr(obj, f)
        return "—"
    safe_date.short_description = "Date"

    def safe_total(self, obj):
        for f in ("total", "amount", "grand_total", "sum"):
            if hasattr(obj, f):
                return getattr(obj, f)
        return "—"
    safe_total.short_description = "Total"
