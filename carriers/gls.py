import os

from requests import Session
from zeep import Client, Transport


async def create_gls_shipment(soap_request_data, username, password, sandbox=False):
    gls_soap_api_url = os.getenv('GLS_SOAP_API_URL')
    gls_client = create_gls_soap_client(gls_soap_api_url)
    gls_soap_payload = soap_to_gls_soap_data(gls_client, soap_request_data)
    gls_soap_response = make_gls_soap_call(gls_client, gls_soap_payload, sandbox=sandbox)
    soap_response = gls_soap_to_soap_data(gls_soap_response)
    return soap_response


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


def gls_soap_to_soap_data(gls_soap_response):
    # Hier wird die Antwort des GLS SOAP-Services in das gewünschte Format umgewandelt
    # Dies ist ein Platzhalter und muss entsprechend der Anforderungen implementiert werden
    soap_response = {
        "Label": gls_soap_response.Label,
        "TrackingNumber": gls_soap_response.TrackingNumber,
        "Status": gls_soap_response.Status
    }
    return soap_response
