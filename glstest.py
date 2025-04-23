import os

from zeep import Client
from zeep.transports import Transport
from requests import Session
import urllib3
import logging.config
from dotenv import load_dotenv
import fitz


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
    wsdl_url = os.getenv("GLS_SOAP_API_URL")

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
    # get_label()

    original = fitz.open("label.pdf")
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
    output = fitz.open()
    new_page = output.new_page(height=label_height, width=label_width)

    # Insert the original page content at the offset defined by the margins
    new_page.show_pdf_page(
        fitz.Rect(margin_left, margin_top, old_width + margin_left, new_height),
        original, 0
    )

    output.save("label_with_margin.pdf")
    print("New PDF with margin saved as label_with_margin.pdf")
