from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import structlog
import requests

from api_dear.models import DearEfrisClientCredentials
from api_mita.services import send_mita_request


struct_logger = structlog.get_logger(__name__)


def process_invoice(response, client_acc_id):
    try:
        # Get local client
        client_data = get_object_or_404(
            DearEfrisClientCredentials, pk=client_acc_id)
        # retrieving invoice data

        task_id = response["SaleTaskID"]
        url = "/sale?ID={}".format(task_id)
        invoice_data = send_dear_api_request(url, client_acc_id)

        goods_details = []
        invoices = invoice_data["Invoices"]

        # retrieving customer data

        url = "/customer?ID={}".format(invoice_data["CustomerID"])
        customer_data = send_dear_api_request(url, client_acc_id)
        customer = customer_data["CustomerList"][0]

        struct_logger.info(
            event="create_outgoing_dear_creditnote",
            invoice_data=invoice_data,
            customer_data=customer,
        )

        # Get variables

        tax_pin = clean_tax_pin(customer, client_data)

        is_export = clean_export(customer, client_data)

        cashier = clean_cashier(response, customer, client_data)

        buyer_type = clean_buyer_type(customer, client_data)

        # Validate tax_pin

        if buyer_type in "0" and tax_pin == "":
            struct_logger.error(
                event="dear_invoice_processing",
                message="Buyer is a business, tax pin should not be empty",
            )

        buyer_details = clean_buyer_details(invoice_data, buyer_type, tax_pin)

        goods_details, invoice = clean_goods_details(invoices)

        tax_invoice = create_mita_invoice(
            invoice,
            invoice_data,
            buyer_details,
            cashier,
            goods_details,
            client_data,
            is_export,
            payment_mode="102",
            invoice_type="1",
            invoice_kind="1",
        )

        struct_logger.info(
            event="dear_invoice_processing",
            message="Sending invoice to mita",
            response=tax_invoice.text,
        )

        return tax_invoice.text

    except Exception as ex:
        struct_logger.error(
            event="dear invoice processing",
            message="Failed to process invoice",
            error=ex,
        )
        return ex


def process_credit_note(response, client_acc_id):
    try:
        # Get local client
        client_data = get_object_or_404(
            DearEfrisClientCredentials, pk=client_acc_id)

        # retrieving credit_note data

        task_id = response["SaleID"]
        url = "/sale/creditnote?SaleID={}".format(task_id)

        invoice_data = send_dear_api_request(url, client_acc_id)

        # invoices = invoice_data["Invoices"]
        credit_notes = invoice_data["CreditNotes"]

        # Old invoice data

        url = "/sale?ID={}".format(task_id)
        invoice_data = send_dear_api_request(url, client_acc_id)

        goods_details = []

        # retrieving customer data

        url = "/customer?ID={}".format(invoice_data["CustomerID"])
        customer_data = send_dear_api_request(url, client_acc_id)
        customer = customer_data["CustomerList"][0]

        struct_logger.info(
            event="create_outgoing_dear_credit_note",
            invoice_data=invoice_data,
            customer_data=customer,
        )

        # Get variables

        tax_pin = clean_tax_pin(customer, client_data)

        is_export = clean_export(customer, client_data)

        cashier = clean_cashier(response, customer, client_data)

        buyer_type = clean_buyer_type(customer, client_data)

        # Validate tax_pin

        if buyer_type in "0" and tax_pin == "":
            struct_logger.error(
                event="create_outgoing_dear_credit_note",
                message="Buyer is a business, tax pin should not be empty",
            )

        buyer_details = clean_buyer_details(invoice_data, buyer_type, tax_pin)

        goods_details, invoice = clean_goods_details(credit_notes)

        tax_invoice = create_mita_invoice(
            invoice,
            invoice_data,
            buyer_details,
            cashier,
            goods_details,
            client_data,
            is_export,
            credit_notes=credit_notes,
        )

        struct_logger.info(
            event="create_outgoing_dear_credit_note",
            message="Sending invoice to mita",
            response=tax_invoice.text,
        )

        return tax_invoice.text

    except Exception as ex:
        struct_logger.error(
            event="dear_invoice_processing",
            message="Sending invoice to mita",
            response=str(ex),
        )
        return str(ex)


def send_dear_api_request(url: str, client_acc_id):
    try:
        # Get local client
        client_data = get_object_or_404(
            DearEfrisClientCredentials, pk=client_acc_id)
        url = "{}/{}".format(client_data.dear_url.dear_url, url)

        account_id = client_data.dear_account_id
        app_key = client_data.dear_app_key

        headers = {"api-auth-accountid": account_id,
                   "api-auth-applicationkey": app_key}
        response = requests.request("GET", url, headers=headers)

        struct_logger.info(
            event="send_dear_request",
            response=response.text,
            msg="Sending dear request",
        )

        return response.json()

    except Exception as ex:
        return {"message": "DEAR URL is unvailable {}".format(str(ex))}


def clean_currency_product(currency):
    if currency == "UGX" or currency == "101":
        return "101"
    elif currency == "USD" or currency == "102":
        return "102"
    elif currency == "EUR" or currency == "104":
        return "104"


def clean_tax_pin(customer, client_data):

    if customer["TaxNumber"]:
        tax_pin = customer["TaxNumber"]
    else:
        tax_pin = customer[client_data.dear_tax_pin_field]

    return tax_pin


def clean_export(customer, client_data):
    return customer[client_data.dear_is_export_field]


def clean_cashier(response, customer, client_data):
    if response["SaleRepEmail"]:
        cashier = response["SaleRepEmail"]
    elif customer["SalesRepresentative"]:
        cashier = customer["SalesRepresentative"]
    else:
        cashier = client_data.dear_default_cashier

    return cashier


def clean_buyer_type(customer, client_data):
    buyer_type = customer[client_data.dear_buyer_type_field]

    if buyer_type.upper() == "B2B":
        return "0"
    elif buyer_type.upper() == "B2C":
        return "1"
    elif buyer_type.upper() == "B2F":
        return "2"
    elif buyer_type.upper() == "B2G":
        return "0"
    else:
        return "1"


def clean_buyer_details(invoice_data, buyer_type, tax_pin):
    buyer_details = {
        "tax_pin": tax_pin,
        "nin": "",
        "passport_number": "",
        "legal_name": invoice_data["Customer"],
        "business_name": invoice_data["Customer"],
        "address": "",
        "email": invoice_data["Email"],
        "mobile": invoice_data["Phone"],
        "buyer_type": buyer_type,
        "buyer_citizenship": "",
        "buyer_sector": "",
        "buyer_reference": invoice_data["Customer"][:45],
        "is_priviledged": False,
    }

    return buyer_details


def clean_goods_details(invoices):
    for invoice in invoices:
        goods = invoice["Lines"]
        goods_details = []
        for item in goods:
            good = {
                "good_code": item["ProductID"],
                "quantity": item["Quantity"],
                "sale_price": item["Price"],
                "tax_category": item["TaxRule"],
            }

            goods_details.append(good)
        return goods_details, invoice


def create_mita_invoice(
    invoice,
    invoice_data,
    buyer_details,
    cashier,
    goods_details,
    client_data,
    is_export=False,
    industry_code="101",
    payment_mode="102",
    invoice_type="1",
    invoice_kind="1",
    credit_notes="",
):
    original_invoice_code = ""
    return_reason = ""
    return_reason_code = ""
    invoice_code = ""
    if is_export == True:
        industry_code = "102"

    if credit_notes:
        for new_credit_note in credit_notes:
            original_invoice_code = new_credit_note["CreditNoteInvoiceNumber"]
            invoice_code = new_credit_note["CreditNoteNumber"]
            return_reason = new_credit_note["TaskID"]
            return_reason_code = "104"
            if new_credit_note["Memo"] in ("101", "102", "103", "104", "105"):
                return_reason_code = new_credit_note["Memo"]

    else:
        invoice_code = invoice["InvoiceNumber"]

    mita_payload = {
        "invoice_details": {
            "invoice_code": invoice_code,
            "cashier": cashier,
            "payment_mode": payment_mode,
            "currency": invoice_data["CustomerCurrency"],
            "invoice_type": invoice_type,
            "invoice_kind": invoice_kind,
            "goods_description": "{}-{}".format(
                invoice_data["Customer"], invoice_data["ID"]
            ),
            "industry_code": industry_code,
            "original_instance_invoice_id": original_invoice_code,
            "return_reason": return_reason,
            "return_reason_code": return_reason_code,
            "is_export": is_export,
        },
        "goods_details": goods_details,
        "buyer_details": {
            "tax_pin": buyer_details["tax_pin"],
            "nin": "",
            "passport_number": "",
            "legal_name": buyer_details["legal_name"],
            "business_name": "",
            "address": "",
            "email": "",
            "mobile": "",
            "buyer_type": buyer_details["buyer_type"],
            "buyer_citizenship": "",
            "buyer_sector": "",
            "buyer_reference": "",
            "is_privileged": buyer_details["is_priviledged"],
            "local_purchase_order": "",
        },
        "instance_invoice_id": invoice_code,
    }
    struct_logger.info(event="sending dear invoice to mita",
                       mita_payload=mita_payload)
    return send_mita_request("invoice/queue?erp=dear", mita_payload, client_data)


def create_goods_configuration(request, client_acc_id):
    # Get local client
    client_data = get_object_or_404(
        DearEfrisClientCredentials, pk=client_acc_id)
    for sku in request:
        try:
            url = "/product?ID={}".format(sku["productID"])

            product_data = send_dear_api_request(url, client_acc_id)

            struct_logger.info(
                event="create_dear_goods_configuration",
                product=product_data,
            )

            product_data = product_data["Products"][0]

            goods_name = sku["productName"]
            goods_code = sku["productName"]
            unit_price = sku["Price"]
            description = product_data[client_data.dear_stock_description_field]
            measure_unit = product_data[client_data.dear_stock_measure_unit_field]
            commodity_category = product_data[
                client_data.dear_stock_commodity_category_field
            ]

            currency = clean_currency_product(
                product_data[client_data.dear_stock_currency_field]
            )

            efris_stock_configuration_payload = {
                "goods_name": goods_name,
                "goods_code": goods_code,
                "unit_price": unit_price,
                "measure_unit": measure_unit,
                "currency": currency,
                "commodity_tax_category": commodity_category,
                "goods_description": description,
            }

            struct_logger.info(
                event="create_dear_goods_configuration",
                efris_product=efris_stock_configuration_payload,
                message="sending dear goods configuration to mita",
            )
            efris_response = send_mita_request(
                "stock/configuration", efris_stock_configuration_payload, client_data
            )
            return HttpResponse(
                "xero Item saved {}  \n EFRIS Item Saved {} ".format(
                    "item", efris_response
                )
            )

        except Exception as ex:
            struct_logger.info(
                event="create_dear_goods_configuration",
                error=str(ex),
                message="Could not configure product",
            )
            return {"sku": sku, "message": "Could not configure product", "error": ex}


def create_goods_adjustment(request, client_acc_id):
    client_data = get_object_or_404(
        DearEfrisClientCredentials, pk=client_acc_id)

    try:
        task_id = request["TaskID"]
        url = "/stockadjustment?TaskID={}".format(task_id)
        stock_data = send_dear_api_request(url, client_acc_id)

        adjusted_stock = stock_data["ExistingStockLines"]

        for stock in adjusted_stock:
            variance = stock["Adjustment"] - stock["QuantityOnHand"]

            if variance > 0:
                operation_type = "101"
                adjust_type = ""
                stock_in_type = "103"
            else:
                operation_type = "102"
                adjust_type = "104"
                stock_in_type = ""

            url = "/product?ID={}".format(stock["ProductID"])
            product_data = send_dear_api_request(url, client_acc_id)
            product_data = product_data["Products"][0]

            struct_logger.info(
                event="dear stock adjustment",
                stock_data=adjusted_stock,
                product_data=product_data,
            )
            efris_stock_adjustment_payload = {
                "goods_code": stock["ProductID"],
                "supplier": "",
                "supplier_tin": "",
                "stock_in_type": stock_in_type,
                "quantity": abs(variance),
                "purchase_price": product_data["AverageCost"],
                "purchase_remarks": stock_data["StocktakeNumber"],
                "operation_type": operation_type,
                "adjust_type": adjust_type,
            }
            struct_logger.info(
                event="create_dear_goods_adjustment",
                efris_product=efris_stock_adjustment_payload,
                message="sending dear goods adjustment to mita",
            )
            efris_response = send_mita_request(
                "stock/adjustment", efris_stock_adjustment_payload, client_data
            )

            return efris_response

    except Exception as ex:
        struct_logger.info(
            event="create_dear_goods_adjustment",
            error=str(ex),
            message="Could not configure product",
        )
        return {
            "sku": product_data,
            "message": "Could not adjust product quantities",
            "error": ex,
        }


def create_goods_stock_in(
    dear_stock, client_acc_id, operation_type="101", adjust_type="", stock_in_type="103"
):
    try:
        client_data = get_object_or_404(
            DearEfrisClientCredentials, pk=client_acc_id)
        for stock in dear_stock:
            struct_logger.info(
                event="dear stock adjustment",
                stock_data=stock,
            )
            efris_stock_adjustment_payload = {
                "goods_code": stock["ID"],
                "supplier": "",
                "supplier_tin": "",
                "stock_in_type": stock_in_type,
                "quantity": stock["OnOrder"],
                "purchase_price": "1000",
                "purchase_remarks": "{}-{}".format(stock["SKU"], stock["Name"]),
                "operation_type": operation_type,
                "adjust_type": adjust_type,
            }
            struct_logger.info(
                event="create_dear_goods_adjustment",
                efris_product=efris_stock_adjustment_payload,
                message="sending dear goods adjustment to mita",
            )
            efris_response = send_mita_request(
                "stock/adjustment", efris_stock_adjustment_payload, client_data
            )

            return efris_response
    except Exception as ex:
        struct_logger.info(
            event="create_dear_goods_adjustment",
            error=str(ex),
            message="Could not configure product",
        )
        return {
            "message": "Could not adjust product quantities",
            "error": ex,
        }
