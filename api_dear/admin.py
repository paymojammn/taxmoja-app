from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    DearCredentials,
    DearEfrisClientCredentials,
    DearEfrisGoodsConfiguration,
    DearEfrisGoodsAdjustment,
    DearOutgoingInvoice,
)

# ---------- Inlines wired to the correct parents ----------


class DearEfrisClientCredentialsInline(admin.TabularInline):
    """
    Works under DearCredentialsAdmin because DearEfrisClientCredentials
    has FK dear_url -> DearCredentials
    """
    model = DearEfrisClientCredentials
    extra = 0
    fields = ("dear_account_id", "dear_app_key", "dear_tax_pin_field")
    show_change_link = True
    # harmless here; allows reuse if needed
    autocomplete_fields = ("dear_url",)


class DearEfrisGoodsConfigurationInline(admin.TabularInline):
    """
    Works under DearEfrisClientCredentialsAdmin because
    DearEfrisGoodsConfiguration has FK client_account -> DearEfrisClientCredentials
    """
    model = DearEfrisGoodsConfiguration
    extra = 0
    fields = ("goods_name", "client_account")
    autocomplete_fields = ("client_account",)
    show_change_link = True


class DearEfrisGoodsAdjustmentInline(admin.TabularInline):
    """
    Optional: show adjustments under GoodsConfiguration admin
    """
    model = DearEfrisGoodsAdjustment
    extra = 0
    fields = ("good",)
    autocomplete_fields = ("good",)
    show_change_link = True


# ---------- Admin registrations ----------

@admin.register(DearCredentials)
class DearCredentialsAdmin(ModelAdmin):
    list_display = ("dear_url", "active", "date_created")
    list_filter = ("active",)
    search_fields = ("dear_url",)
    ordering = ("-date_created",)
    inlines = [DearEfrisClientCredentialsInline]  # ✅ fixed: correct inline

    fieldsets = (
        ("DEAR Account", {"fields": ("dear_url", "active")}),
        ("Timestamps", {"fields": ("date_created",),
         "classes": ("collapse",)}),
    )
    readonly_fields = ("date_created",)

    @admin.action(description="Activate selected credentials")
    def activate(self, request, queryset):
        queryset.update(active=True)

    @admin.action(description="Deactivate selected credentials")
    def deactivate(self, request, queryset):
        queryset.update(active=False)

    actions = ("activate", "deactivate")


@admin.register(DearEfrisClientCredentials)
class DearEfrisClientCredentialsAdmin(ModelAdmin):
    list_display = (
        "dear_url",
        "dear_account_id",
        "dear_app_key",
        "dear_tax_pin_field",
    )
    list_filter = ("dear_url",)
    search_fields = (
        "dear_account_id",
        "dear_app_key",
        "dear_tax_pin_field",
        "dear_buyer_type_field",
        "dear_default_cashier",
    )
    autocomplete_fields = ("dear_url",)
    ordering = ("dear_account_id",)
    # ✅ fixed: configs inline here
    inlines = [DearEfrisGoodsConfigurationInline]

    fieldsets = (
        ("Linkage", {"fields": ("dear_url",)}),
        ("DEAR API / Account",
         {"fields": ("dear_account_id", "dear_app_key")}),
        ("Customer Fields", {
            "fields": (
                "dear_tax_pin_field",
                "dear_buyer_type_field",
                "dear_is_export_field",
                "dear_default_cashier",
            )
        }),
        ("Stock Field Mapping", {
            "fields": (
                "dear_stock_description_field",
                "dear_stock_measure_unit_field",
                "dear_stock_commodity_category_field",
                "dear_stock_currency_field",
                "dear_stock_in_price_field",
            )
        }),
    )


@admin.register(DearEfrisGoodsConfiguration)
class DearEfrisGoodsConfigurationAdmin(ModelAdmin):
    list_display = ("goods_name", "client_account_display")
    list_filter = ("client_account__dear_url",)
    search_fields = ("goods_name", "client_account__dear_account_id")
    autocomplete_fields = ("client_account",)
    inlines = [DearEfrisGoodsAdjustmentInline]

    fieldsets = (
        ("Good", {"fields": ("goods_name",)}),
        ("Linkage", {"fields": ("client_account",)}),
    )

    @admin.display(description="Client account")
    def client_account_display(self, obj):
        return str(obj.client_account) if obj.client_account_id else "—"


@admin.register(DearEfrisGoodsAdjustment)
class DearEfrisGoodsAdjustmentAdmin(ModelAdmin):
    list_display = ("good_name", "good")
    list_filter = ("good__client_account__dear_url",)
    search_fields = ("good__goods_name",)
    autocomplete_fields = ("good",)

    fieldsets = (("Adjustment", {"fields": ("good",)}),)

    @admin.display(description="Goods name")
    def good_name(self, obj):
        return obj.good.goods_name if getattr(obj, "good_id", None) else "—"


@admin.register(DearOutgoingInvoice)
class DearOutgoingInvoiceAdmin(ModelAdmin):
    list_display = ("pk", "date_created")  # ✅ fixed: use pk, not id
    ordering = ("-date_created",)
    readonly_fields = ("date_created",)

    fieldsets = (
        # extend with fields from parent if needed
        ("Invoice", {"fields": ()}),
        ("Timestamps", {"fields": ("date_created",)}),
    )
