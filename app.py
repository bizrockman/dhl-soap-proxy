import os
import json
import xml.etree.ElementTree as ET
import logging

import pycountry
import httpx
import xmltodict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from zeep import Client
from zeep.transports import Transport
from requests import Session


logging.basicConfig(
    filename='logs/my_app.log',  # Pfad zur Log-Datei
    filemode='a',  # 'a' für append, 'w' zum Überschreiben
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formatierung der Log-Nachrichten
    level=logging.DEBUG  # Minimallevel für die Erfassung von Nachrichten
)


load_dotenv()
dhl_api_key = os.getenv('DHL_API_KEY')
app = FastAPI()


def get_rest_api_base_url(sandbox=False):
    if sandbox:
        return os.getenv('DHL_SANDBOX_REST_API_URL')
    else:
        return os.getenv('DHL_PRODUCTION_REST_API_URL')


def get_rest_api_orders_url(sandbox=False):
    dhl_rest_api_base_url = get_rest_api_base_url(sandbox)
    return f"{dhl_rest_api_base_url}orders"


@app.get("/")
async def test_dhl_api():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                get_rest_api_base_url(sandbox=True),
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
    payload = get_test_rest_object(package_type='klp')
    print(payload)
    username = os.getenv('GKP_SANDBOX_USER')
    password = os.getenv('GKP_SANDBOX_PASSWORD')
    dhl_rest_api_orders_url = get_rest_api_orders_url(sandbox=True)
    response = await make_rest_api_call(dhl_rest_api_orders_url, payload, username, password)
    print(response.json())
    response = JSONResponse(content=response.json())
    return response


async def make_rest_api_call(rest_api_url, payload, username, password):
    headers = {
        "accept": "application/json",
        "Accept-Language": "de-DE",
        "Content-Type": "application/json",
        "dhl-api-key": dhl_api_key
    }
    auth = (username, password)

    async with httpx.AsyncClient() as client:
        response = await client.post(rest_api_url, json=payload, headers=headers, auth=auth,
                                     params={"validate": "False", "includeDocs": "URL", "printFormat": "910-300-700"})
        return response


def get_test_rest_object(package_type='nat'):
    if package_type == 'nat':
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
    elif package_type == 'klp':
        payload = {
            "profile": "STANDARD_GRUPPENPROFIL",
            "shipments": [
                {
                    "product": "V62KP",
                    "billingNumber": "33333333336201",
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
    else:
        payload = {
            "profile": "STANDARD_GRUPPENPROFIL",
            "shipments": [
                {
                    "product": "V62KP",
                    "billingNumber": "33333333336202",
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


def create_gls_soap_client(gls_soap_api_url) -> Client:
    session = Session()
    session.headers.update({
        "Authorization": "Basic " + os.getenv("GLS_AUTH"),
        "Requester": "bizness rocket GmbH"
    })
    session.verify = False

    client = Client(wsdl=gls_soap_api_url, transport=Transport(session=session))

    return client


def soap_to_gls_soap_data(gls_client, soap_request_data):
    factory = gls_client.type_factory("ns0")
    common = gls_client.type_factory("ns1")

    consignee = common.Consignee(Address=common.Address(
        Name1="Max Mustermann",
        Street="Musterstraße",
        StreetNumber="12",
        ZIPCode="12345",
        City="Musterstadt",
        CountryCode="DE"
    ))

    # Adresse Versender (ContactID nötig!)
    shipper = common.Shipper(ContactID=os.getenv("GLS_CLIENT_ID"))

    # Paketinhalt
    shipment_unit = factory.ShipmentUnit(Weight=1.5)

    # Gesamt-Sendung
    shipment = factory.Shipment(
        Product='Parcel',
        Consignee=consignee,
        Shipper=shipper,
        ShipmentUnit=[shipment_unit]
    )

    return shipment


def make_gls_soap_call(gls_client, gls_soap_payload, sandbox=False):
    factory = gls_client.type_factory("ns0")

    # Druckoptionen
    printing_options = factory.PrintingOptions(
        ReturnLabels=factory.ReturnLabels(
            TemplateSet="NONE",
            LabelFormat="PDF"
        )
    )

    try:
        # service = client.bind("ShipmentProcessingPortType", "ShipmentProcessingServiceSoapBinding")
        service = gls_client.service
        result = service.createParcels(
            Shipment=gls_soap_payload,
            PrintingOptions=printing_options
        )

        return result
    except Exception as e:
        print("Fehler beim Erstellen des Versandlabels:", str(e))


def soap_to_rest_data(xml_data, sandbox=False):
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
            consignee["name1"] = inner_person.get("ns1:firstname", '') + " " + inner_person.get("ns1:lastname", '')
        else:
            raise HTTPException(status_code=400, detail="Invalid SOAP request: Inner Company / Person missing.")
    else:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Company missing.")

    consignee['addressStreet'] = receiver['Address']['ns1:streetName']

    consignee['addressHouse'] = receiver.get('Address').get('ns1:streetNumber', '')
    additional_address_information = receiver.get('Address').get('ns1:additionalAddressInformation', '')
    if additional_address_information:
        if not consignee.get("name2"):
            consignee['name2'] = additional_address_information
        else:
            consignee['name3'] = additional_address_information

    care_of_name = receiver.get('Address').get('ns1:careOfName', '')
    if care_of_name:
        if not consignee.get("name2"):
            consignee['name2'] = care_of_name
        else:
            consignee['name3'] = care_of_name

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
    if consignee.get('contactName') and len(consignee['contactName']) > 3:
        # consignee['contactName'] = consignee['name1']
        if not consignee.get("name2"):
            consignee['name2'] = consignee['contactName']
        else:
            consignee['name3'] = consignee['contactName']
        #del (consignee['contactName'])

    consignee['phone'] = receiver['Communication']['ns1:phone']

    #    if 'Packstation' in consignee['addressStreet']:
    #        consignee['name2'] = consignee['contactName']
    #        del(consignee['contactName'])

    if consignee.get('contactName') and len(consignee['contactName']) < 3:
        del (consignee['contactName'])

        # Details
    details = {
        "weight": {
            "uom": "kg",
            "value": float(shipment_details.get('ShipmentItem').get('WeightInKG'))
        }
    }

    if sandbox:
        ekp = os.getenv('EKP_TEST')
    else:
        ekp = os.getenv('EKP')

    product_code = shipment_details.get('ProductCode')
    if product_code == 'EPN':  # DHL Paket
        product_code = 'V01PAK'
        billing_number = ekp + os.getenv('DHL_BILLING_NUMBER_NAT_PREFIX')
    elif product_code == 'BPI':  # Weltpaket
        product_code = 'V53WPAK'
        billing_number = ekp + os.getenv('DHL_BILLING_NUMBER_INTL_PREFIX')
    elif product_code == 'EPI':  # Europaket
        product_code = 'V54EPAK'
        billing_number = ekp + os.getenv('DHL_BILLING_NUMBER_INTL_PREFIX')
    elif product_code == 'KLP':  # Kleinpaket
        product_code = 'V62KP'
        billing_number = ekp + os.getenv('DHL_BILLING_NUMBER_KLP_PREFIX')
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
    if status and isinstance(status, dict):
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
    label_url = None
    shipment_no = None

    if items:
        shipment_no = items[0].get("shipmentNo")
        if items[0].get("label"):
            label_url = rest_data.get("items")[0].get("label").get("url")

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
        ET.SubElement(shipment_number, f"{{{namespaces['cis']}}}shipmentNumber").text = shipment_no

        # PieceInformation Element
        piece_information = ET.SubElement(creation_state, "PieceInformation")
        piece_number = ET.SubElement(piece_information, "PieceNumber")
        ET.SubElement(piece_number, f"{{{namespaces['cis']}}}licensePlate").text = shipment_no

        # Labelurl
        if label_url:
            ET.SubElement(creation_state, "Labelurl").text = label_url

    # Baum in eine Zeichenfolge umwandeln
    xml_str = ET.tostring(envelope, encoding="utf-8")
    return xml_str


def get_carrier_code_from_product_code(xml_data):
    shipment_order = xml_data.get("ShipmentOrder")
    if not shipment_order:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: ShipmentOrder missing.")

    shipment = shipment_order.get("Shipment")
    if not shipment:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Shipment missing.")

    shipment_details = shipment.get("ShipmentDetails")
    if not shipment_details:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: ShipmentDetails missing.")

    product_code = shipment_details.get('ProductCode')
    return product_code


async def create_shipment(soap_request_data, username, password, sandbox=False):
    carrier = get_carrier_code_from_product_code(soap_request_data)

    if carrier == 'GLS':
        soap_response = await create_gls_shipment(soap_request_data, username, password, sandbox=sandbox)
    else:
        soap_response = await create_dhl_shipment(soap_request_data, username, password, sandbox=sandbox)
    return soap_response


async def create_gls_shipment(soap_request_data, username, password, sandbox=False):
    gls_soap_api_url = os.getenv('GLS_SOAP_API_URL')
    gls_client = create_gls_soap_client(gls_soap_api_url)
    gls_soap_payload = soap_to_gls_soap_data(gls_client, soap_request_data)
    gls_soap_response = make_gls_soap_call(gls_client, gls_soap_payload, sandbox=sandbox)
    soap_response = gls_soap_to_soap_data(gls_soap_response)
    return soap_response


async def create_dhl_shipment(soap_request_data, username, password, sandbox=False):
    dhl_rest_api_orders_url = get_rest_api_orders_url(sandbox=sandbox)
    payload = soap_to_rest_data(soap_request_data, sandbox)
    print(payload)
    response = await make_rest_api_call(dhl_rest_api_orders_url, payload, username, password)
    print(response.status_code)
    print(response.json())
    soap_response = rest_to_soap_data(response.status_code, response.json())
    print(soap_response)
    return soap_response

@app.post("/production/soap")
async def handle_production_soap_request(request: Request):
    response = await handle_soap_request(request, sandbox=False)
    return response


@app.post("/sandbox/soap")
async def handle_sandbox_soap_request(request: Request):
    response = await handle_soap_request(request, sandbox=True)
    return response


async def handle_soap_request(request: Request, sandbox=False):
    soap_request_data = await request.body()
    soap_request_dict = xmltodict.parse(soap_request_data, encoding="utf-8")
    logging.debug(f"SOAP Request DATA: {json.dumps(soap_request_dict, indent=2)}")

    envelope = soap_request_dict.get("SOAP-ENV:Envelope")
    if not envelope:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Envelope missing.")

    header = envelope.get("SOAP-ENV:Header")
    if not header:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Header missing.")

    auth = header.get("ns1:Authentification")
    if not auth:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Authentification missing.")

    if sandbox:
        username = os.getenv('GKP_SANDBOX_USER')
        password = os.getenv('GKP_SANDBOX_PASSWORD')
    else:
        username = auth.get("ns1:user")
        password = auth.get("ns1:signature")
        if not username and not password:
            username = os.getenv('GKP_USER')
            password = os.getenv('GKP_PASSWORD')

    body = envelope.get("SOAP-ENV:Body")
    if not body:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Body missing.")

    method_name, method_data = next(iter(body.items()))

    if method_name.endswith("CreateShipmentDDRequest"):
        logging.debug(f"SOAP Method: {method_name} - Wird verarbeitet.")
        response_data = await create_shipment(method_data, username, password, sandbox=sandbox)
        logging.debug(f"SOAP Response DATA: {response_data}")
    else:
        # Für alle anderen Methoden, die nicht unterstützt werden oder unbekannt sind
        raise HTTPException(status_code=400, detail=f"Unsupported SOAP method: {method_name}")

    headers = {"Content-Type": "application/xml"}
    response = Response(content=response_data, media_type="application/xml", headers=headers)
    return response
