import json
import requests
import structlog

from api_mita.models import MitaCredentials

struct_logger = structlog.get_logger(__name__)


def send_mita_request(url_ext, payload, client_account):
    # Sends request to mita-api
    mita_credentials = MitaCredentials.objects.filter(active=True).first()

    struct_logger.info(
        event="send_mita_request",
        url_ext=url_ext,
        payload=payload,
        client_account=client_account,
    )
    mita_url = mita_credentials.mita_url
    url = "{}/{}".format(mita_url, url_ext)
    headers = {
        "x-tax-id": "{}".format(client_account.tax_pin),
        "x-api-token": "{}".format(client_account.tax_pin),
        "x-tax-country-code": "{}".format(client_account.mita_country_code),
        "x-api-key-header": "{}".format(client_account.mita_api_header),
        "Content-Type": "application/json",
    }

    payload = json.dumps(payload)

    response = requests.request("POST", url, headers=headers, data=payload)

    struct_logger.info(
        event="send_mita_request",
        payload=payload,
        response=response.text,
        msg="Sending request to mita",
    )

    return response


def create_mita_invoice(
    mita_invoice,
    client_data,
    payment_mode="102",
    industry_code="101",
    invoice_type="1",
    invoice_kind="1",
    is_priviledged=False,
    is_export=False,
):
    # Mita Payload Sample

    # invoice_type
    #  1:Invoice/Receipt
    # 5:Credit Memo/rebate
    # 4:Debit Note

    # invoice_kind

    # 1: invoice 2: receipt

    # Industry code

    # 101:General Industry 102:Export 104:Imported Service 105:Telecom 106:Stamp Duty 107:Hotel Service 108:Other taxes 109:Airline Business 110:EDC

    # Payment mode

    # payWay dictionary table 101 Credit
    # 102 Cash
    # 103 Cheque
    # 104 Demand draft 105 Mobile money 106 Visa/Master card 107 EFT
    # 108 POS
    # 109 RTGS
    # 110 Swift transfer

    # mita_invoice = {
    #     "invoice_id": "",
    #     "cashier": "",
    #     "currency_code": "",
    #     "goods_description": "",
    #     "original_instance_invoice_id": "",
    #     "return_reason": "",
    #     "return_reason_code": "",
    #     "seller_reference": "",
    #     "goods_details": [],
    #     "buyer_tax_pin": "",
    #     "legal_name": "",
    #     "buyer_type": "",
    # "local_purchase_order":"",
    # "buyer_email":"",
    # "buyer_address":""
    # }

    # "edcDetails":{
    #     "tankNo": "1111",
    #     "pumpNo": "2222",
    #     "nozzleNo": "3333",
    #     "controllerNo": "44444",
    #     "acquisitionEquipmentNo": "5555",
    #     "levelGaugeNo": "66666",
    #     "mvrn":""
    # }

    mita_payload = {
        "invoice_details": {
            "invoice_code": mita_invoice["invoice_id"],
            "cashier": mita_invoice["cashier"],
            "payment_mode": payment_mode,
            "currency": mita_invoice["currency_code"],
            "invoice_type": invoice_type,
            "invoice_kind": invoice_kind,
            "goods_description": mita_invoice["goods_description"],
            "industry_code": industry_code,
            "original_instance_invoice_id": mita_invoice[
                "original_instance_invoice_id"
            ],
            "return_reason": mita_invoice["return_reason"],
            "return_reason_code": mita_invoice["return_reason_code"],
            "is_export": is_export,
        },
        "sellers_details": {
            "reference_no": mita_invoice["seller_reference"],
        },
        "goods_details": mita_invoice["goods_details"],
        "buyer_details": {
            "tax_pin": mita_invoice["buyer_tax_pin"],
            "nin": "",
            "passport_number": "",
            "legal_name": mita_invoice["legal_name"],
            "business_name": mita_invoice["legal_name"],
            "address": "",
            "email": mita_invoice[" buyer_email"],
            "mobile": "",
            "buyer_type": mita_invoice[" buyer_type"],
            "buyer_citizenship": "",
            "buyer_sector": "",
            "buyer_reference": "",
            "is_privileged": is_priviledged,
            "local_purchase_order": mita_invoice["local_purchase_order"],
        },
        "edc_details": mita_invoice["edc_details"],
        "instance_invoice_id": mita_invoice["invoice_id"],
    }

    send_mita_request("invoice/queue", mita_payload, client_data)


def create_goods_configuration(mita_goods_config, client_data):
    pass


def create_goods_adjustment(
    mita_goods_stockin,
    client_data,
    stock_in_type="102",
    adjust_type="",
    operation_type="101",
):
    # mita_goods_stockin = {
    #     "goods_code": "",
    #     "supplier": "",
    #     "supplier_tin": "",
    #     "quantity": "",
    #     "purchase_price": "",
    #     "purchase_remarks": "",
    # }

    # operationType: 101:Increase inventory 102:Inventory reduction

    #     101:Expired Goods
    #     102:Damaged Goods
    #     103:Personal Uses
    #     105:Raw Material(s)
    #     104:Others. (Please specify)
    #     If operationType = 101， adjustType must be empty
    #     If operationType = 102， adjustType cannot be empty

    #     stock in type
    #     101:Import
    #     102:Local Purchase
    #     103:Manufacture/Assembling
    #     104:Opening Stock
    # If operationType = 101， stockInType cannot be empty
    # If operationType = 102， stockInType must be empty

    efris_stock_adjustment_payload = {
        "goods_code": mita_goods_stockin["goods_code"],
        "supplier": mita_goods_stockin["supplier"],
        "supplier_tin": mita_goods_stockin["supplier_tin"],
        "stock_in_type": stock_in_type,
        "quantity": mita_goods_stockin["quantity"],
        "purchase_price": mita_goods_stockin["purchase_price"],
        "purchase_remarks": mita_goods_stockin["purchase_remarks"],
        "operation_type": operation_type,
        "adjust_type": adjust_type,
    }

    send_mita_request("stock/adjustment",
                      efris_stock_adjustment_payload, client_data)
