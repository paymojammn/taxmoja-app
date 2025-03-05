from http.client import BAD_REQUEST, HTTPResponse
import os
import structlog
from django.http import HttpResponse
import json
import base64
import dateutil.parser
from xero import Xero
from manager_efris.models import (
    EfrisCommodityCategories,
    EfrisCurrencyCodes,
    EfrisMeasureUnits,
)
from api_xero.models import XeroEfrisClientCredentials, XeroEfrisGoodsConfiguration
from xero.auth import OAuth2Credentials
from api_mita.services import send_mita_request
from django.shortcuts import get_object_or_404

import datetime
struct_logger = structlog.get_logger(__name__)


def create_xero_goods_configuration(good_instance):
    try:
        struct_logger.info(
            event="create_xero_goods_configuration",
            product=good_instance,
        )
        goods_name = good_instance["goods_name"]
        goods_code = good_instance["goods_code"]
        purchase_price = good_instance["unit_price"]
        unit_price = good_instance["unit_price"]
        description = good_instance["description"]

        currency = get_object_or_404(
            EfrisCurrencyCodes, pk=good_instance["currency_id"]
        )
        measure_unit = get_object_or_404(
            EfrisMeasureUnits, pk=good_instance["measure_unit_id"]
        )
        efris_commodity_tax_category = get_object_or_404(
            EfrisCommodityCategories, pk=good_instance["commodity_tax_category_id"]
        )
        client_data = get_object_or_404(
            XeroEfrisClientCredentials, pk=good_instance["client_account_id"]
        )

        xero_tax_rate = client_data.xero_standard_tax_rate_code
        if efris_commodity_tax_category.tax_rate == 0.00:
            xero_tax_rate = client_data.xero_exempt_tax_rate_code
        xero_purchase_account_code = client_data.xero_purchase_account
        is_product = True
        is_purchased = True

        new_product = {
            "Code": goods_code,
            "PurchaseDetails": {
                "UnitPrice": purchase_price,
                "AccountCode": xero_purchase_account_code,
                "TaxType": xero_tax_rate,
            },
            "SalesDetails": {
                "UnitPrice": unit_price,
                "AccountCode": xero_purchase_account_code,
                "TaxType": xero_tax_rate,
            },
            "Name": goods_name,
            "IsTrackedAsInventory": is_product,
            "IsSold": True,
            "IsPurchased": is_purchased,
        }

        struct_logger.info(
            event="create_xero_goods_configuration",
            client_data=client_data.cred_state,
            account=good_instance,
        )

        credentials = xero_client_credentials(client_data)
        xero = Xero(credentials)
        item = xero.items.put(new_product)

        struct_logger.info(
            event="create_xero_goods_configuration",
            xero_product=item,
            account=good_instance,
        )

        efris_stock_configuration_payload = {
            "goods_name": goods_name,
            "goods_code": goods_code,
            "unit_price": str(unit_price),
            "measure_unit": measure_unit.measure_unit_code,
            "currency": currency.currency_code,
            "commodity_tax_category": efris_commodity_tax_category.efris_commodity_category_code,
            "goods_description": description,
        }

        struct_logger.info(
            event="create_xero_goods_configuration",
            efris_product=efris_stock_configuration_payload,
            account=good_instance,
        )
        efris_response = send_mita_request(
            "stock/configuration", efris_stock_configuration_payload, client_data
        )
        return HttpResponse(
            "xero Item saved {}  \n EFRIS Item Saved {} ".format(
                item, efris_response)
        )
    except Exception as ex:
        struct_logger.error(
            event="create_xero_goods_configuration",
            error=ex,
        )
        return HttpResponse("Error in Goods Configuration {}   ".format(str(ex)))


def efris_bulk_configure_goods(client_data):

    try:
        credentials = xero_client_credentials(client_data)
        xero = Xero(credentials)
        items = xero.items.all()

        efris_commodity_category = "50131701"  # Replace with actual logic
        currency = "101"  # Replace with actual logic
        measure_unit = "PP"  # Replace with actual logic

        for item in items:
            print(item)
            efris_stock_configuration_payload = {
                "goods_name": item.get("Name"),
                "goods_code": item.get("Code"),
                "unit_price": str(item.get("PurchaseDetails", {}).get("UnitPrice", 0)),
                "measure_unit": measure_unit,
                "currency": currency,
                "commodity_tax_category": efris_commodity_category,
                "goods_description": item.get("Name"),
            }

            struct_logger.info(
                event="bulk_xero_goods_configuration",
                efris_product=efris_stock_configuration_payload,
                item=item,
            )
            efris_response = send_mita_request(
                "stock/configuration", efris_stock_configuration_payload, client_data
            )

            print(efris_response)

    except Exception as e:
        return {"error": str(e)}


def efris_bulk_adjust_goods(client_data):

    try:
        credentials = xero_client_credentials(client_data)
        xero = Xero(credentials)
        items = xero.items.all()
        purchase_price = '5000.00'
        supplier = 'Vital Tomosis'
        supplier_tin = '1003841291'
        quantity = '2000000'
        stock_in_type = '101'
        adjust_type = ''
        operation_type = '101'
        purchase_remarks = 'Initial Stock'

        for item in items:
            efris_stock_adjustment_payload = {
                "goods_code": item.get("Code"),
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
                "stock/adjustment", efris_stock_adjustment_payload, client_data
            )

        return {"success": "All items adjusted successfully"}

    except Exception as e:
        return {"error": str(e)}


def create_xero_goods_adjustment(good_instance):
    try:
        struct_logger.info(
            event="create_xero_goods_adjustment",
            product=good_instance,
        )

        xero_invoice_type = good_instance["xero_invoice_type"]

        purchase_price = good_instance["purchase_price"]
        supplier = good_instance["supplier"]
        supplier_tin = good_instance["supplier_tin"]
        quantity = good_instance["quantity"]
        stock_in_type = good_instance["stock_in_type"]
        adjust_type = good_instance["adjust_type"]
        operation_type = good_instance["operation_type"]
        purchase_remarks = good_instance["purchase_remarks"]

        goods_details = get_object_or_404(
            XeroEfrisGoodsConfiguration, pk=good_instance["good_id"]
        )

        client_data = goods_details.client_account
        cred_state = goods_details.client_account.cred_state
        credentials = xero_client_credentials(client_data)
        xero = Xero(credentials)

        contact = xero.contacts.all()[0]
        xero_tax_rate = client_data.xero_standard_tax_rate_code
        if goods_details.commodity_tax_category.tax_rate == 0.00:
            xero_tax_rate = client_data.xero_exempt_tax_rate_code
        goods_code = goods_details.goods_code

        line_items = []

        if adjust_type is None:
            adjust_type = ""

        line_item = {
            "ItemCode": goods_code,
            "Description": purchase_remarks,
            "Quantity": quantity,
            "UnitAmount": purchase_price,
            "TaxType": xero_tax_rate,
            "AccountCode": client_data.xero_purchase_account,
        }

        line_items.append(line_item)

        invoice_date = datetime.datetime.utcnow().isoformat() + "Z"

        invoice = {
            "LineItems": line_items,
            "Contact": contact,
            "DueDate": dateutil.parser.parse(invoice_date),
            "Date": dateutil.parser.parse(invoice_date),
            "Type": xero_invoice_type,
            "Status": "AUTHORISED",
        }

        invoice = xero.invoices.put(invoice)

        struct_logger.info(
            event="create_xero_goods_adjustment",
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
            "stock/adjustment", efris_stock_adjustment_payload, client_data
        )

        return HTTPResponse(
            "xero Adjustment saved {}  \n Efris Item Saved {} ".format(
                invoice, mita_stock
            )
        )

    except Exception as ex:
        struct_logger.error(
            event="create_xero_goods_adjustment",
            error=str(ex),
        )
        return HttpResponse("Error in Goods Adjustment {}   ".format(str(ex)))


def xero_send_invoice_data(request, client_data):
    try:
        data = json.loads(request.decode("utf8").replace("'", '"'))
        print(data)
        data = data["events"][0]
        invoice_id = data["resourceId"]
        event_type = data["eventType"]
        event_category = data["eventCategory"]
        tenant_id = data["tenantId"]

        struct_logger.info(
            event="xero_incoming_invoice",
            xero_data=data,
            dt=data,
            invoice_id=invoice_id,
            event_type=event_type,
            event_category=event_category,
        )

        credentials = xero_client_credentials(client_data)
        xero = Xero(credentials)

        invoices = xero.invoices.get("{}".format(invoice_id))

        struct_logger.info(
            event="xero_incoming_invoice",
            message="invoices retrived",
            invoice_data=invoices,
        )

        generate_mita_invoice(invoices, client_data)

        return HttpResponse("invoices retrieved {}".format(invoices))

    except Exception as ex:
        return HttpResponse("invoices not retrieved {}".format(str(ex)))


def generate_mita_invoice(xero_invoices, client_data):

    struct_logger.info(
        event="generate_mita_invoice",
        invoice_data=xero_invoices,
    )

    for xero_invoice in xero_invoices:
        struct_logger.info(
            event="generate_mita_invoice",
            message="generating mita invoice:{}".format(
                xero_invoice["InvoiceNumber"]),
            invoice_data=xero_invoice,
        )

        try:

            if xero_invoice["Status"] in ("AUTHORISED", "PAID"):

                print(xero_invoice["Status"])

                try:

                    if xero_invoice["CreditNotes"]:
                        struct_logger.info(
                            event="generate_mita_invoice", message="sending credit notes for generation", credit_notes=xero_invoice["CreditNotes"], invoice=xero_invoice)
                        return generate_mita_credit_note(xero_invoice, client_data)
                except KeyError:
                    pass

                is_export = False
                is_priviledged = False
                goods_details = []
                contact_groups = xero_invoice["Contact"]["ContactGroups"]
                buyer_type, buyer_tax_pin = get_client_tax_credentials(
                    contact_groups, xero_invoice)

                for good in xero_invoice["LineItems"]:
                    mita_good = {
                        "good_code": good["ItemCode"],
                        "quantity": good["Quantity"],
                        "sale_price": good["UnitAmount"],
                        "tax_category": good["TaxType"],
                    }
                    goods_details.append(mita_good)

                    mita_payload = {
                        "invoice_details": {
                            "invoice_code": xero_invoice["InvoiceNumber"],
                            "cashier": "System",
                            "payment_mode": "107",
                            "currency": xero_invoice["CurrencyCode"],
                            "invoice_type": "1",
                            "invoice_kind": "1",
                            "goods_description": xero_invoice["Reference"],
                            "industry_code": "",
                            "original_instance_invoice_id": "",
                            "return_reason": "",
                            "return_reason_code": "",
                            "is_export": is_export,
                        },
                        "goods_details": goods_details,
                        "buyer_details": {
                            "tax_pin": buyer_tax_pin,
                            "nin": "",
                            "passport_number": "",
                            "legal_name": xero_invoice["Contact"]["Name"],
                            "business_name": "",
                            "address": "",
                            "email": "",
                            "mobile": "",
                            "buyer_type": buyer_type,
                            "buyer_citizenship": "",
                            "buyer_sector": "",
                            "buyer_reference": "",
                            "is_privileged": is_priviledged,
                            "local_purchase_order": "",
                        },
                        "instance_invoice_id": xero_invoice["InvoiceNumber"],
                    }
                    struct_logger.info(
                        event="sending xero invoice to mita", mita_payload=mita_payload
                    )

                    send_mita_request(
                        "invoice/queue", mita_payload, client_data)
        except Exception as ex:
            struct_logger.error(
                event="generate_mita_invoice",
                error=ex,
            )
            return HttpResponse("Error in invoice generation {}   ".format(str(ex)))


def generate_mita_credit_note(credited_xero_invoice, client_data):

    try:
        xero_credit_notes = credited_xero_invoice["CreditNotes"]

        credentials = xero_client_credentials(client_data)
        xero = Xero(credentials)

        for xero_invoice in xero_credit_notes:

            struct_logger.info(
                event="generate_mita_credit_note",
                message="generating mita credit note:{}".format(
                    xero_invoice["CreditNoteNumber"]),
                invoice_data=xero_invoice,
            )
            credit_notes = xero.creditnotes.get(
                "{}".format(xero_invoice["ID"]))

            is_export = False
            is_priviledged = False
            goods_details = []
            contact_groups = credited_xero_invoice["Contact"]["ContactGroups"]
            original_invoice_number = credited_xero_invoice["InvoiceNumber"]
            buyer_type, buyer_tax_pin = get_client_tax_credentials(
                contact_groups, xero_invoice)

            attachments = []

            struct_logger.info(
                event="generate_mita_credit_note",
                message="retrieving credit note",
                credit_note_id=xero_invoice["CreditNoteID"],
                credit_note_number=xero_invoice["CreditNoteNumber"],
                credit_note=credit_notes
            )
            for credit_note in credit_notes:
                struct_logger.info(
                    event="generate_mita_credit_note",
                    message="retrieving credit note",
                    credit_note=credit_note,
                )
                try:

                    if credit_note['HasAttachments']:
                        for attachment in credit_note["Attachments"]:
                            attachment_data = xero.creditnotes.get_attachment_data(
                                credit_note["CreditNoteID"], attachment["AttachmentID"]
                            )

                            attachment_base64 = base64.b64encode(
                                attachment_data).decode("utf-8")
                            file_name = attachment["FileName"]
                            with open(file_name, "wb") as file:
                                file.write(attachment_data)
                            file_name, file_extension = os.path.splitext(
                                file_name)

                            attachment = {
                                "fileName": file_name, "fileType": file_extension.lstrip("."), "fileContent": attachment_base64}

                            attachments.append(attachment)

                            # Save the attachment locally
                            # Ensure file name is extracted correctly

                            struct_logger.info(
                                event="xero_incoming_credit_note",
                                message=f"Retrieved credit note attachment: {file_name}",
                                encoded_data=attachment_base64,
                            )

                except KeyError:
                    pass

                for good in credit_note["LineItems"]:
                    mita_good = {
                        "good_code": good["ItemCode"],
                        "quantity": good["Quantity"],
                        "sale_price": good["UnitAmount"],
                        "tax_category": good["TaxType"],
                    }
                    goods_details.append(mita_good)

                mita_payload = {
                    "invoice_details": {
                        "invoice_code": credit_note["CreditNoteNumber"],
                        "cashier": "System",
                        "payment_mode": "107",
                        "currency": credit_note["CurrencyCode"],
                        "invoice_type": "1",
                        "invoice_kind": "1",
                        "goods_description": credit_note["CreditNoteID"],
                        "industry_code": "",
                        "original_instance_invoice_id": original_invoice_number,
                        "return_reason": credit_note["Reference"],
                        "return_reason_code": "105",
                        "is_export": is_export,
                    },
                    "goods_details": goods_details,
                    "buyer_details": {
                        "tax_pin": buyer_tax_pin,
                        "nin": "",
                        "passport_number": "",
                        "legal_name": credit_note["Contact"]["Name"],
                        "business_name": "",
                        "address": "",
                        "email": "",
                        "mobile": "",
                        "buyer_type": buyer_type,
                        "buyer_citizenship": "",
                        "buyer_sector": "",
                        "buyer_reference": "",
                        "is_privileged": is_priviledged,
                        "local_purchase_order": "",
                    },
                    "attachments": attachments,
                    "instance_invoice_id": credit_note["CreditNoteNumber"],
                }
                struct_logger.info(
                    event="sending xero credit note to mita", mita_payload=mita_payload
                )

                send_mita_request(
                    "invoice/queue", mita_payload, client_data)

    except Exception as ex:
        struct_logger.error(
            event="generate_mita_invoice",
            error=ex,
        )
        return HttpResponse("Error in credit note generation {}   ".format(str(ex)))


def xero_client_credentials(client_data):
    cred_state = client_data.cred_state
    credentials = OAuth2Credentials(**cred_state)
    if credentials.expired():
        credentials.refresh()
        client_data.cred_state = credentials.state
        client_data.save()
    return credentials


def get_client_tax_credentials(contact_groups, xero_invoice):
    try:
        buyer_tax_pin = ""
        buyer_type = "0"
        if contact_groups[0]["Name"] in ("Business", "business", "Government"):
            buyer_type = "0"

        elif contact_groups[0]["Name"] == "Foreignor":
            buyer_type = "2"

        else:
            buyer_type = "1"

        buyer_tax_pin = xero_invoice["Contact"]["TaxNumber"]

        return buyer_type, buyer_tax_pin

    except Exception as ex:
        buyer_type = "1"
        buyer_tax_pin = ""

        return buyer_type, buyer_tax_pin
