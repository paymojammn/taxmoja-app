# admin.py
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    OEEfrisClientCredentials,
    OEEfrisGoodsConfiguration,
    OEEfrisGoodsAdjustment,
    OEOutgoingInvoice,
)

# ---- Optional branding (you can also use UNFOLD settings in settings.py) ----
admin.site.site_header = "Centry"
admin.site.site_title = "Centry Admin"
admin.site.index_title = "Welcome to Centry"


# ---------- Client Credentials ----------
@admin.register(OEEfrisClientCredentials)
class OEEfrisClientCredentialsAdmin(ModelAdmin):
    list_display = (
        "id",
        "company_name",
        "oe_url",
        "active",
    )
    search_fields = ("company_name", "oe_url")
    list_filter = ("active",)
    readonly_fields = ("id",)
    ordering = ("company_name",)
    list_per_page = 50

    fieldsets = (
        ("Company", {"fields": ("company_name", "active")}),
        ("OpenEngage / OE", {"fields": ("oe_url", "oe_api_key")}),
        ("Default Stock Configuration", {
            "fields": (
                "stock_configuration_measure_unit",
                "stock_configuration_currency",
                "stock_configuration_unit_price",
                "stock_configuration_commodity_category",
            )
        }),
    )


# ---------- Goods Configuration ----------
@admin.register(OEEfrisGoodsConfiguration)
class OEEfrisGoodsConfigurationAdmin(ModelAdmin):
    list_display = (
        "id",
        "goods_name",
        "goods_code",
        "commodity_tax_category",
        "unit_price",
        "currency",
        "measure_unit",
        "client_account",
    )
    search_fields = ("goods_name", "goods_code", "commodity_tax_category")
    list_filter = ("commodity_tax_category", "currency",
                   "measure_unit", "client_account")
    readonly_fields = ("id",)
    ordering = ("goods_name",)
    list_per_page = 50


# ---------- Goods Adjustment ----------
@admin.register(OEEfrisGoodsAdjustment)
class OEEfrisGoodsAdjustmentAdmin(ModelAdmin):
    """
    NOTE: In your model, `good` points to OEEfrisClientCredentials.
    But __str__ tries to access `self.good.goods_name`, which doesn't exist on credentials.
    Until the model is adjusted, we display a safe label here.
    """
    list_display = ("id", "safe_good_label",)
    search_fields = ()
    list_filter = ()
    readonly_fields = ("id",)
    list_per_page = 50

    def safe_good_label(self, obj):
        # Show company name if `good` is a credentials record; fall back gracefully.
        if obj.good:
            # OEEfrisClientCredentials likely has company_name
            return getattr(obj.good, "company_name", str(obj.good))
        return "—"
    safe_good_label.short_description = "Good / Client"


# ---------- Outgoing Invoice ----------
@admin.register(OEOutgoingInvoice)
class OEOutgoingInvoiceAdmin(ModelAdmin):
    list_display = ("safe_invoice_number", "date_created")
    search_fields = ("invoice_number",)  # if parent model defines this
    list_filter = ("date_created",)
    readonly_fields = ["date_created"]
    ordering = ("-date_created",)
    list_per_page = 50

    def safe_invoice_number(self, obj):
        # If the base model defines invoice_number or similar, show it; else show ID.
        return getattr(obj, "invoice_number", f"Invoice #{obj.id}")
    safe_invoice_number.short_description = "Invoice Number"
