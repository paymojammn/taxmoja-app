import base64
import hashlib
import hmac
from http import client
import json

import dateutil.parser
from urllib.parse import urlparse
from urllib.parse import parse_qs

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.cache import caches, cache
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from xero import Xero
from xero.auth import OAuth2Credentials
from xero.constants import XeroScopes
from .models import ClientCredentials

from django.core.exceptions import BadRequest

import structlog

struct_logger = structlog.get_logger(__name__)


def create_xero_goods_configuration(good_instance):
    try:
        struct_logger.info(event='create_xero_goods_configuration',
                           product=good_instance,
                           )
        goods_name = good_instance['goods_name']
        goods_code = good_instance['goods_code']
        purchase_price = good_instance['unit_price']
        unit_price = good_instance['unit_price']
        currency = good_instance['currency']
        measure_unit = good_instance['measure_unit']
        commodity_tax_category = good_instance['commodity_tax_category']
        xero_tax_rate = good_instance['xero_tax_rate']
        description = good_instance['description']
        account_code = good_instance['xero_purchase_account']
        client_account_id = good_instance['client_account_id']
        is_product = True
        is_purchased = True

        new_product = {

            "Code": goods_code,

            "PurchaseDetails": {
                "UnitPrice": purchase_price,
                "AccountCode": account_code,
                "TaxType": xero_tax_rate
            },
            "SalesDetails": {
                "UnitPrice": unit_price,
                "AccountCode": account_code,
                "TaxType": xero_tax_rate
            },
            "Name": goods_name,
            "IsTrackedAsInventory": is_product,
            "IsSold": True,
            "IsPurchased": is_purchased
        }

        client_data = get_client_data(client_account_id)

        cred_state = client_data.cred_state
        credentials = OAuth2Credentials(**cred_state)

        struct_logger.info(event='create_xero_goods_configuration', client_data=client_data.cred_state,
                           account=good_instance, credentials=type(credentials))

        if credentials.expired():
            credentials.refresh()
            client_data.cred_state = credentials.state
            client_data.save()

        xero = Xero(credentials)
        item = xero.items.put(new_product)

        struct_logger.info(event='create_xero_goods_configuration',
                           xero_product=item, account=good_instance)

        efris_stock_configuration_payload = {
            "goods_name": goods_name,
            "goods_code": goods_code,
            "unit_price": unit_price,
            "measure_unit": measure_unit,
            "currency": currency,
            "commodity_tax_category": commodity_tax_category,
            "goods_description": description
        }

        struct_logger.info(event='create_xero_goods_configuration',
                           efris_product=efris_stock_configuration_payload,
                           account=good_instance
                           )
        efris_response = send_mita_request(
            'stock/configuration', efris_stock_configuration_payload, client_data)
        return HttpResponse("xero Item saved {}  \n EFRIS Item Saved {} ".format(item, efris_response))
    except Exception as ex:
        struct_logger.error(event='create_xero_goods_configuration',
                            error=ex,

                            )
        return HttpResponse("Error in Goods Configuration {}   ".format(str(ex)))


def create_xero_goods_adjustment(good_instance):
    try:

        struct_logger.info(event=create_xero_goods_adjustment,
                           product=good_instance,
                           )

        xero_invoice_type = good_instance['xero_invoice_type']
        goods_code = good_instance['goods_code']
        purchase_price = good_instance['purchase_price']
        supplier = good_instance['supplier']
        supplier_tin = good_instance['supplier_tin']
        quantity = good_instance['quantity']
        stock_in_type = good_instance['stock_in_type']
        adjust_type = good_instance['adjust_type']
        operation_type = good_instance['operation_type']
        purchase_remarks = good_instance['purchase_remarks']
        xero_tax_rate = good_instance['xero_tax_rate']
        account_code = good_instance['xero_purchase_account']
        currency = good_instance['currency']
        client_account_id = good_instance['client_account_id']

        line_items = []

        if adjust_type is None:
            adjust_type = ""

        client_data = get_client_data(client_account_id)

        cred_state = client_data.cred_state
        credentials = OAuth2Credentials(**cred_state)
        if credentials.expired():
            credentials.refresh()
            client_data.cred_state = credentials.state
            client_data.save()
        xero = Xero(credentials)

        contact = xero.contacts.get(u'39efa556-8dda-4c81-83d3-a631e59eb6d3')

        line_item = {
            "ItemCode": goods_code,
            "Description": purchase_remarks,
            "Quantity": quantity,
            "UnitAmount": purchase_price,
            "TaxType": xero_tax_rate,
            "AccountCode": "300"
        }

        line_items.append(line_item)

        invoice = {
            "LineItems": line_items,
            "Contact": contact,
            "DueDate": dateutil.parser.parse("2020-09-03T00:00:00Z"),
            "Date": dateutil.parser.parse("2020-07-03T00:00:00Z"),
            "Type": xero_invoice_type,
            "Status": "AUTHORISED"
        }

        invoice = xero.invoices.put(invoice)

        struct_logger.info(event=create_xero_goods_adjustment,
                           xero_invoice=invoice,
                           )

        efris_stock_adjustment_payload = {
            "goods_code": goods_code,
            "supplier": supplier,
            "supplier_tin": supplier_tin,
            "stock_in_type": stock_in_type,
            "quantity": quantity,
            "purchase_price": purchase_price,
            "purchase_remarks": purchase_remarks,
            "operation_type": operation_type,
            "adjust_type": adjust_type,
        }

        mita_stock = send_mita_request(
            'stock/adjustment', efris_stock_adjustment_payload, client_data)

        return HttpResponse("xero Adjustment saved {}  \n Efris Item Saved {} ".format(invoice, mita_stock))

    except Exception as ex:
        struct_logger.error(event=create_xero_goods_adjustment,
                            error=str(ex),

                            )


def xero_get_contacts(request, client_data):
    # cred_state = cache.get('xero_creds')
    cred_state = client_data.cred_state
    credentials = OAuth2Credentials(**cred_state)
    if credentials.expired():
        credentials.refresh()
        client_data.cred_state = credentials.state
        client_data.save()
    xero = Xero(credentials)

    contacts = xero.contacts.get(u'39efa556-8dda-4c81-83d3-a631e59eb6d3')
    print(contacts)

    return HttpResponse("contacts retrieved {}".format(contacts))


def xero_get_items(request):
    # cred_state = cache.get('xero_creds')
    cred_state = client_data.cred_state
    credentials = OAuth2Credentials(**cred_state)
    if credentials.expired():
        credentials.refresh()
        client_data.cred_state = credentials.state
        client_data.save()
    xero = Xero(credentials)

    items = xero.items.all()
    print(items)

    return HttpResponse("items retrieved {}".format(items))


def xero_put_item(request):
    item = {

        "Code": "ntinda_102",

        "PurchaseDetails": {
            "UnitPrice": "2000",
            "AccountCode": "300",
            "TaxType": "TAX004"
        },
        "SalesDetails": {
            "UnitPrice": "3000",
            "AccountCode": "300",
            "TaxType": "TAX004"
        },
        "Name": "ntinda",
        "IsTrackedAsInventory": True,
        "IsSold": True,
        "IsPurchased": True
    }

    cred_state = client_data.cred_state
    credentials = OAuth2Credentials(**cred_state)
    if credentials.expired():
        credentials.refresh()
        client_data.cred_state = credentials.state
        client_data.save()
    xero = Xero(credentials)

    item = xero.items.put(item)

    return HttpResponse("items retrieved {}".format(item))
