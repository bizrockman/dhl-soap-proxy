import os

from zeep import Client
from zeep.transports import Transport
from requests import Session
import urllib3
import logging.config
from dotenv import load_dotenv


# logging.config.dictConfig({
#     'version': 1,
#     'formatters': {
#         'verbose': {
#             'format': '%(name)s: %(message)s'
#         }
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         }
#     },
#     'loggers': {
#         'zeep.transports': {
#             'level': 'DEBUG',
#             'handlers': ['console']
#         }
#     }
# })
# Zertifikatswarnungen unterdrücken (nur für Entwicklung)
urllib3.disable_warnings()


def get_label():
    wsdl_url = "https://shipit-wbm-de06.gls-group.eu:443/backend/ShipmentProcessingService/ShipmentProcessingPortType?wsdl"

    session = Session()
    session.headers.update({
        "Authorization": "Basic "+os.getenv("GLS_AUTH"),
        "Requester": "bizness rocket GmbH"
    })
    session.verify = False

    client = Client(wsdl=wsdl_url, transport=Transport(session=session))
    factory = client.type_factory("ns0")
    common = client.type_factory("ns1")

    # Adresse Empfänger
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

    # Druckoptionen
    printing_options = factory.PrintingOptions(
        ReturnLabels=factory.ReturnLabels(
            TemplateSet="NONE",
            LabelFormat="PDF"
        )
    )

    try:
        #service = client.bind("ShipmentProcessingPortType", "ShipmentProcessingServiceSoapBinding")
        service = client.service
        result = service.createParcels(
            Shipment=shipment,
            PrintingOptions=printing_options
        )

        for doc in result.PrintData:
            # print(doc.Data)
            # pdf_data = base64.b64decode(doc.Data)
            pdf_data = doc.Data
            with open("label.pdf", "wb") as f:
                f.write(pdf_data)
            print("PDF gespeichert unter label.pdf")

    except Exception as e:
        print("Fehler beim Erstellen des Versandlabels:", str(e))


if __name__ == "__main__":
    load_dotenv()
    get_label()
