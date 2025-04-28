import os
import fitz
from uuid import uuid4
import xml.etree.ElementTree as ET

from requests import Session
from zeep import Client, Transport

from fastapi import HTTPException, Request


async def create_gls_shipment(soap_request_data, base_url, sandbox=False):
    gls_soap_api_url = os.getenv('GLS_SOAP_API_URL')
    gls_client = create_gls_soap_client(gls_soap_api_url)
    gls_soap_payload = soap_to_gls_soap_data(gls_client, soap_request_data)
    gls_soap_response = make_gls_soap_call(gls_client, gls_soap_payload, sandbox=sandbox)
    gls_soap_response_w_url = save_attachment_and_get_url(gls_soap_response, base_url)
    soap_response = gls_soap_to_soap_data(gls_soap_response_w_url)
    return soap_response


def save_attachment_and_get_url(gls_soap_response, base_url):
    filename = f"label_{uuid4()}.pdf"
    label_dir = os.getenv("GLS_LABELS_FOLDER", 'labels')
    os.makedirs(label_dir, exist_ok=True)

    filepath = os.path.join(label_dir, filename)

    output = fitz.open()

    for doc in gls_soap_response.PrintData:
        # print(doc.Data)
        pdf_data = doc.Data
        original = fitz.open(stream=pdf_data, filetype="pdf")

        page = original[0]

        # Extra margins in points (1 cm = 28.3465 pt)
        margin_left = 2.8 * 28.3465
        margin_top = 2 * 28.3465

        label_width = 15.0 * 28.3465  # 15 cm in points
        label_height = 20.8 * 28.3465  # 10 cm in points

        old_width, old_height = page.rect.width, page.rect.height
        new_width = old_width + margin_left
        new_height = old_height + margin_top

        # Create new PDF with larger page size
        # output = fitz.open()
        new_page = output.new_page(height=label_height, width=label_width)

        # Insert the original page content at the offset defined by the margins
        new_page.show_pdf_page(
            fitz.Rect(margin_left, margin_top, old_width + margin_left, new_height),
            original, 0
        )

        output.save(filepath)

    # Exchange PrintData Data with the URL
    gls_soap_response.PrintData = []
    gls_soap_response.LabelURL = f"{base_url}label/gls/{filename}"
    return gls_soap_response


def create_gls_soap_client(gls_soap_api_url) -> Client:
    session = Session()
    session.headers.update({
        "Authorization": "Basic " + os.getenv("GLS_AUTH"),
        "Requester": "bizness rocket GmbH"
    })
    session.verify = False

    client = Client(wsdl=gls_soap_api_url, transport=Transport(session=session))

    return client


def soap_to_gls_soap_data(gls_client, xml_data):
    shipment_order = xml_data.get("ShipmentOrder")
    if not shipment_order:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: ShipmentOrder missing.")

    shipment = shipment_order.get("Shipment")
    if not shipment:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Shipment missing.")

    shipment_details = shipment.get("ShipmentDetails")
    if not shipment_details:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: ShipmentDetails missing.")

    receiver = shipment.get("Receiver")
    if not receiver:
        raise HTTPException(status_code=400, detail="Invalid SOAP request: Receiver missing.")

    factory = gls_client.type_factory("ns0")
    common = gls_client.type_factory("ns1")

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

    # consignee['addressStreet'] = receiver['Address']['ns1:streetName']
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
    consignee['country'] = country_iso_code

    consignee['contactName'] = receiver['Communication']['ns1:contactPerson']
    if consignee.get('contactName') and len(consignee['contactName']) > 3:
        # consignee['contactName'] = consignee['name1']
        if not consignee.get("name2"):
            consignee['name2'] = consignee['contactName']
        else:
            consignee['name3'] = consignee['contactName']
        # del (consignee['contactName'])

    consignee['phone'] = receiver['Communication']['ns1:phone']

    #    if 'Packstation' in consignee['addressStreet']:
    #        consignee['name2'] = consignee['contactName']
    #        del(consignee['contactName'])

    if consignee.get('contactName') and len(consignee['contactName']) < 3:
        del (consignee['contactName'])

    consignee = common.Consignee(Address=common.Address(
        Name1=consignee.get("name1"),
        Name2=consignee.get("name2"),
        CountryCode=consignee.get("country"),
        ZIPCode=consignee.get("postalCode"),
        City=consignee.get("city"),
        Street=consignee.get("addressStreet"),
        StreetNumber=consignee.get("addressHouse"),
        ContactPerson=consignee.get("contactName"),
        FixedLinePhonenumber=consignee.get("phone"),
    ))

    # Adresse Versender (ContactID nötig!)
    shipper = common.Shipper(ContactID=os.getenv("GLS_CLIENT_ID"))

    # Paketinhalt
    weight = float(shipment_details.get('ShipmentItem').get('WeightInKG'))
    shipment_unit = factory.ShipmentUnit(Weight=weight)

    # Gesamt-Sendung
    shipment = factory.Shipment(
        ShipmentReference=shipment_details.get('CustomerReference'),
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
        raise HTTPException(status_code=500, detail=f"Error creating GLS shipment: {str(e)}")


def gls_soap_to_soap_data(gls_soap_response):
    print(gls_soap_response)

    status_code = 0
    status_name = 'ok'
    shipment_no = gls_soap_response.ParcelData[0].TrackID

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
    #if items:
        # CreationState Element
    creation_state = ET.SubElement(create_shipment_response, "CreationState")
    ET.SubElement(creation_state, "StatusCode").text = status_code
    ET.SubElement(creation_state, "StatusMessage").text = status_name
    #if validation_messages:
    #    for validation_message in validation_messages:
    #        ET.SubElement(creation_state, "StatusMessage").text = validation_message

    ET.SubElement(creation_state, "SequenceNumber").text = "1"
    shipment_number = ET.SubElement(creation_state, "ShipmentNumber")
    ET.SubElement(shipment_number, f"{{{namespaces['cis']}}}shipmentNumber").text = shipment_no

    # PieceInformation Element
    piece_information = ET.SubElement(creation_state, "PieceInformation")
    piece_number = ET.SubElement(piece_information, "PieceNumber")
    ET.SubElement(piece_number, f"{{{namespaces['cis']}}}licensePlate").text = shipment_no

    # Labelurl
    if gls_soap_response.LabelURL:
        ET.SubElement(creation_state, "LabelURL").text = gls_soap_response.LabelURL

    # Baum in eine Zeichenfolge umwandeln
    xml_str = ET.tostring(envelope, encoding="utf-8")
    return xml_str
