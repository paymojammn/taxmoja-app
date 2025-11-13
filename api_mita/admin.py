# admin.py
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import MitaCredentials

# --- Optional branding (or configure via UNFOLD in settings.py) ---
admin.site.site_header = "Centry"
admin.site.site_title = "Centry Admin"
admin.site.index_title = "Welcome to Centry"


@admin.register(MitaCredentials)
class MitaCredentialsAdmin(ModelAdmin):
    list_display = ("id", "mita_url", "active", "date_created")
    search_fields = ("mita_url",)
    list_filter = ("active", "date_created")
    ordering = ("-date_created",)
    readonly_fields = ("id", "date_created")
    list_per_page = 50
