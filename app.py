import os
import json
import logging
import xmltodict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse

from carriers.dhl import test_dhl_api, create_dhl_test_shipment, create_dhl_shipment
from carriers.gls import create_gls_shipment

from utils.proxy_middelware import ProxiedHeadersMiddleware

logging.basicConfig(
    filename='logs/my_app.log',  # Pfad zur Log-Datei
    filemode='a',  # 'a' für append, 'w' zum Überschreiben
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formatierung der Log-Nachrichten
    level=logging.DEBUG  # Minimallevel für die Erfassung von Nachrichten
)


load_dotenv()
app = FastAPI()
app.add_middleware(ProxiedHeadersMiddleware)  # type: ignore[arg-type]


@app.get("/health")
async def health_check(request: Request):
    #get base url
    base_url = request.base_url
    return {"base_url": base_url, "status": "ok"}

@app.get("/")
async def test_dhl_api():
    return await test_dhl_api()


@app.post("/test/create-shipment")
async def create_test_shipment(request: Request):
    return await create_dhl_test_shipment(request)


@app.get("/label/gls/{filename}")
async def download_label(file_name: str):
    file_path = os.path.join("/tmp/labels", file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type='application/pdf', filename=file_name)


async def create_shipment(soap_request_data, username, password, sandbox=False):
    carrier = get_carrier_code_from_product_code(soap_request_data)

    if carrier == 'GLS':
        soap_response = await create_gls_shipment(soap_request_data, username, password, sandbox=sandbox)
    else:
        soap_response = await create_dhl_shipment(soap_request_data, username, password, sandbox=sandbox)
    return soap_response


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
