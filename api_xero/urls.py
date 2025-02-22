from django.urls import path, re_path

from . import views

urlpatterns = [
    path('<int:client_acc_id>/', views.start_xero_auth_view,
         name='xero_authentication_view'),
    path('callback/<int:client_acc_id>',
         views.process_callback_view, name='xero_callback_process'),
    path('webhook/<int:client_acc_id>',
         views.xero_invoice_webhook, name='xero_webhook'),
    path('bulk_goods_configure/<int:client_acc_id>',
         views.xero_bulk_products_configuration, name='xero_efris_product_config'),
    path('bulk_goods_adjust/<int:client_acc_id>',
         views.xero_bulk_products_adjustment, name='xero_efris_product_adjustment'),


]
