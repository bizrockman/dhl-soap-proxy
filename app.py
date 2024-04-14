import os
import json
import xml.etree.ElementTree as ET
import logging

import pycountry
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Request, Response
import httpx
import xmltodict

logging.basicConfig(
    filename='logs/my_app.log',  # Pfad zur Log-Datei
    filemode='a',  # 'a' für append, 'w' zum Überschreiben
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formatierung der Log-Nachrichten
    level=logging.DEBUG  # Minimallevel für die Erfassung von Nachrichten
)

load_dotenv()
dhl_api_key = os.getenv('DHL_API_KEY')
dhl_rest_api_base_url = os.getenv('DHL_REST_API_URL')
dhl_rest_api_orders_url = f"{dhl_rest_api_base_url}orders"

gkp_user = os.getenv('GKP_USER')
gkp_password = os.getenv('GKP_PASSWORD')

app = FastAPI()


@app.get("/")
async def test_dhl_api():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                dhl_rest_api_base_url,
                headers={
                    "accept": "application/json",
                    "dhl-api-key": dhl_api_key
                }
            )
            # Prüfe den Statuscode der Antwort
            if response.status_code == 200:
                response_dict = {"message": "DHL API ist erreichbar."}
                response_dict.update(response.json())
                return response_dict
            else:
                return {"message": "DHL API ist nicht erreichbar.", "status_code": response.status_code}
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Anfragefehler: {str(e)}")


@app.post("/test/create-shipment")
async def create_test_shipment(request: Request):
    payload = get_test_rest_object()
    response = await make_rest_api_call(dhl_rest_api_orders_url, payload)
    print(response)
    return response


async def make_rest_api_call(rest_api_url, payload, username=None, password=None):
    headers = {
        "accept": "application/json",
        "Accept-Language": "de-DE",
        "Content-Type": "application/json",
        "dhl-api-key": dhl_api_key
    }

    if username and password:
        auth = (username, password)
    else:
        auth = (gkp_user, gkp_password)

    async with httpx.AsyncClient() as client:
        response = await client.post(rest_api_url, json=payload, headers=headers, auth=auth,
                                     params={"validate": "False", "includeDocs": "URL", "printFormat": "910-300-700"})
        return response
        #if response.status_code == 200:
            # Gib die Antwort von DHL API zurück
        #    return response.json()
        #else:
            # Bei einem Fehler gib den Statuscode und die Fehlermeldung zurück
        #    return HTTPException(status_code=response.status_code, detail=response.text)


def get_test_rest_object():
    payload = {
        "profile": "STANDARD_GRUPPENPROFIL",
        "shipments": [
            {
                "product": "V01PAK",
                "billingNumber": "33333333330102",
                "refNo": "Order No. 1234",
                "shipper": {
                    "name1": "My Online Shop GmbH",
                    "addressStreet": "Sträßchensweg 10",
                    "additionalAddressInformation1": "2. Etage",
                    "postalCode": "53113",
                    "city": "Bonn",
                    "country": "DEU",
                    "email": "max@mustermann.de",
                    "phone": "+49 123456789"
                },
                "consignee": {
                    "name1": "Maria Musterfrau",
                    "addressStreet": "Kurt-Schumacher-Str. 20",
                    "additionalAddressInformation1": "Apartment 107",
                    "postalCode": "53113",
                    "city": "Bonn",
                    "country": "DEU",
                    "email": "maria@musterfrau.de",
                    "phone": "+49 987654321"
                },
                "details": {
                    "weight": {
                        "uom": "g",
                        "value": 500
                    }
                }
            }
        ]
    }
    return payload


def get_iso3_from_iso2(country_iso2_code):
    country = pycountry.countries.get(alpha_2=country_iso2_code)
    if country:
        return country.alpha_3
    else:
        raise ValueError("Invalid country ISO2 code.")


def soap_to_rest_data(xml_data):
    shipment_order = xml_data.get("ShipmentOrder")
    if not shipment_order:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: ShipmentOrder missing.")

    shipment = shipment_order.get("Shipment")
    if not shipment:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Shipment missing.")

    shipment_details = shipment.get("ShipmentDetails")
    if not shipment_details:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: ShipmentDetails missing.")

    shipper = shipment.get("Shipper")
    if not shipper:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Shipper missing.")

    receiver = shipment.get("Receiver")
    if not receiver:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Receiver missing.")

    # Absender
    shipper = {
        "name1": shipper["Company"]["ns1:Company"]["ns1:name1"],
        "name2": shipper["Company"]["ns1:Company"]["ns1:name2"],
        "addressStreet": shipper["Address"]["ns1:streetName"],
        "addressHouse": shipper["Address"]["ns1:streetNumber"],
        "postalCode": shipper["Address"]["ns1:Zip"]["ns1:germany"],
        "city": shipper["Address"]["ns1:city"],
        "country": shipper["Address"]["ns1:Origin"]["ns1:countryISOCode"],
        "email": shipper["Communication"]["ns1:email"],
        "phone": shipper["Communication"]["ns1:phone"],
        "contactName": shipper["Communication"]["ns1:contactPerson"]
    }

    country_iso_code = shipper['country']
    country = pycountry.countries.get(alpha_2=country_iso_code)
    if country:
        shipper['country'] = country.alpha_3
    else:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Country ISO code missing or not valid.")

    # Adressat
    consignee = {}
    company = receiver.get("Company")
    if company:
        inner_company = company.get("ns1:Company")
        inner_person = company.get("ns1:Person")
        if inner_company:
            consignee["name1"] = inner_company.get("ns1:name1", '')
            if inner_company.get("ns1:name2"):
                consignee["name2"] = inner_company.get("ns1:name2")
        elif inner_person:
            consignee["name1"] = inner_person.get("ns1:firstname",'') + " " + inner_person.get("ns1:lastname", '')
        else:
            raise HTTPException(status_code=400, detail="Invalid SOAP request: Inner Company / Person missing.")
    else:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Company missing.")

    consignee['addressStreet'] = receiver['Address']['ns1:streetName']

    consignee['addressHouse'] = receiver.get('Address').get('ns1:streetNumber', '')
    additional_address_information = receiver.get('Address').get('ns1:additionalAddressInformation', '')
    if additional_address_information:
        consignee['additionalAddressInformation'] = additional_address_information

    postal_code_german_destination = receiver['Address']['ns1:Zip'].get('ns1:germany')
    if postal_code_german_destination:
        postal_code = postal_code_german_destination
    else:
        postal_code = receiver['Address']['ns1:Zip']['ns1:other']

    if not postal_code:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Postal code missing.")
    else:
        consignee['postalCode'] = postal_code

    consignee['city'] = receiver['Address']['ns1:city']

    country_iso_code = receiver['Address']['ns1:Origin']['ns1:countryISOCode']
    country = pycountry.countries.get(alpha_2=country_iso_code)
    if country:
        consignee['country'] = country.alpha_3
    else:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Country ISO code missing or not valid.")

    consignee['contactName'] = receiver['Communication']['ns1:contactPerson']
    if consignee['contactName'] and len(consignee['contactName']) < 3:
        consignee['contactName'] = consignee['name1']
    consignee['phone'] = receiver['Communication']['ns1:phone']

    if 'Packstation' in consignee['addressStreet']:
        consignee['name2'] = consignee['contactName']
        del(consignee['contactName'])

        # Details
    details = {
        "weight": {
            "uom": "kg",
            "value": float(shipment_details.get('ShipmentItem').get('WeightInKG'))
        }
    }

    product_code = shipment_details.get('ProductCode')
    if product_code == 'EPN':  # DHL Paket
        product_code = 'V01PAK'
        billing_number = os.getenv('DHL_BILLING_NUMBER_NAT')
    elif product_code == 'BPI':  # Weltpaket
        product_code = 'V53WPAK'
        billing_number = os.getenv('DHL_BILLING_NUMBER_INTL')
    elif product_code == 'EPI':  # Europaket
        product_code = 'V54EPAK'
        billing_number = os.getenv('DHL_BILLING_NUMBER_INTL')
    else:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Product code missing or not valid.")

    json_data = {
        "profile": "STANDARD_GRUPPENPROFIL",
        "shipments": [
            {
                "product": product_code,
                "billingNumber": billing_number,
                "refNo": shipment_details.get('CustomerReference'),
                #"shipDate": shipment_details.get('ShipmentDate'),
                "shipper": shipper,
                "consignee": consignee,
                "details": details,
            }
        ]
    }

    return json_data


def rest_to_soap_data(response_statuscode, rest_data):

    status = rest_data.get("status")
    if status:
        status_name = status.get("title").lower()
    else:
        status_name = rest_data.get("title").lower()

    validation_messages = []

    if response_statuscode == 200:
        status_code = "0"

    elif response_statuscode == 401:
        if 'unauthorized' in status_name:
            status_code = "1001"
            status_name = 'login failed'
            validation_messages.append(rest_data.get('detail'))
        else:
            raise HTTPException(status_code=401, detail="Unknown 401 Status Code Issue")
    else:
        status_code = "1101"
        status_name = 'Hard validation error occured.'
        validation_message = rest_data.get("items")[0].get("validationMessage")
        if validation_message:
            validation_message = validation_message.get('validationMessage')

    items = rest_data.get("items")

    if items:
        shipmentNo = items[0].get("shipmentNo")
        if items[0].get("label"):
            labelUrl = rest_data.get("items")[0].get("label").get("url")
        else:
            labelUrl = None

        if items[0].get("validationMessages"):
            for validation_message in items[0].get("validationMessages"):
                message = validation_message.get("validationMessage")
                if validation_message.get("validationState") == "Warning":
                    validation_messages.append(message)
                else:
                    validation_messages.insert(0, message)


    # Namensräume definieren
    namespaces = {
        'soapenv': "http://schemas.xmlsoap.org/soap/envelope/",
        'cis': "http://dhl.de/webservice/cisbase",
        'is': "http://de.ws.intraship"
    }
    # Alle Namensräume für die Verwendung im Dokument registrieren
    for ns in namespaces:
        ET.register_namespace(ns, namespaces[ns])

    # Wurzelelement erstellen
    envelope = ET.Element(f"{{{namespaces['soapenv']}}}Envelope")

    # Header und Body erstellen
    header = ET.SubElement(envelope, f"{{{namespaces['soapenv']}}}Header")
    body = ET.SubElement(envelope, f"{{{namespaces['soapenv']}}}Body")

    # CreateShipmentResponse Element
    create_shipment_response = ET.SubElement(body, f"{{{namespaces['is']}}}CreateShipmentResponse")

    # Version Element
    version = ET.SubElement(create_shipment_response, f"{{{namespaces['cis']}}}Version")
    ET.SubElement(version, f"{{{namespaces['cis']}}}majorRelease").text = "1"
    ET.SubElement(version, f"{{{namespaces['cis']}}}minorRelease").text = "0"
    ET.SubElement(version, f"{{{namespaces['cis']}}}build").text = "14"

    # Status Element
    status = ET.SubElement(create_shipment_response, "status")
    ET.SubElement(status, "StatusCode").text = status_code
    ET.SubElement(status, "StatusMessage").text = status_name

    # ShipmentNumber Element
    if items:
        # CreationState Element
        creation_state = ET.SubElement(create_shipment_response, "CreationState")
        ET.SubElement(creation_state, "StatusCode").text = status_code
        ET.SubElement(creation_state, "StatusMessage").text = status_name
        if validation_messages:
            for validation_message in validation_messages:
                ET.SubElement(creation_state, "StatusMessage").text = validation_message

        ET.SubElement(creation_state, "SequenceNumber").text = "1"
        shipment_number = ET.SubElement(creation_state, "ShipmentNumber")
        ET.SubElement(shipment_number, f"{{{namespaces['cis']}}}shipmentNumber").text = shipmentNo

        # PieceInformation Element
        piece_information = ET.SubElement(creation_state, "PieceInformation")
        piece_number = ET.SubElement(piece_information, "PieceNumber")
        ET.SubElement(piece_number, f"{{{namespaces['cis']}}}licensePlate").text = shipmentNo

        # Labelurl
        if labelUrl:
            ET.SubElement(creation_state, "Labelurl").text = labelUrl

    # Baum in eine Zeichenfolge umwandeln
    xml_str = ET.tostring(envelope, encoding="utf-8")
    return xml_str  # xml_str.decode("utf-8")


async def create_shipment(soap_request_data, username, password):
    payload = soap_to_rest_data(soap_request_data)
    print(payload)
    response = await make_rest_api_call(dhl_rest_api_orders_url, payload, username, password)
    print(response.status_code)
    print(response.json())
    soap_response = rest_to_soap_data(response.status_code, response.json())
    print(soap_response)
    return soap_response


@app.post("/soap")
async def handle_soap_request(request: Request):
    soap_request_data = await request.body()
    soap_request_dict = xmltodict.parse(soap_request_data, encoding="utf-8")
    logging.debug(f'SOAP Request DATA: {json.dumps(soap_request_dict, indent=2)}')

    envelope = soap_request_dict.get("SOAP-ENV:Envelope")
    if not envelope:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Envelope missing.")

    header = envelope.get("SOAP-ENV:Header")
    if not header:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Header missing.")

    auth = header.get("ns1:Authentification")
    if not auth:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Authentification missing.")

    #username = auth.get("ns1:user")
    #password = auth.get("ns1:signature")
    username = None
    password = None

    body = envelope.get("SOAP-ENV:Body")
    if not body:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Body missing.")

    method_name, method_data = next(iter(body.items()))

    if method_name.endswith("CreateShipmentDDRequest"):
        logging.debug(f"SOAP Method: {method_name} - Wird verarbeitet.")
        response_data = await create_shipment(method_data, username, password)
        logging.debug(f"SOAP Response DATA: {response_data}")
    else:
        # Für alle anderen Methoden, die nicht unterstützt werden oder unbekannt sind
        raise HTTPException(status_code=400, detail=f"Unsupported SOAP method: {method_name}")

    headers = {"Content-Type": "application/xml"}
    response = Response(content=response_data, media_type="application/xml", headers=headers)
    return response
