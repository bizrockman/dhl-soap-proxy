# DHL SOAP to REST Proxy
(German Translation below)

With this project, you can continue to use your applications that still rely on the DHL SOAP API, saving time for migration. Initially, only SOAP API v1 has been implemented, which will be discontinued on 31.05.2024.

This project provides a framework to also make SOAP API v2 and SOAP API v3 usable.

## Functionality

This is a simple proxy that accepts SOAP requests and forwards them to the DHL REST API v2.1. The response is received and then encapsulated back into a SOAP request, which is returned to the client. The proxy is a simple FastAPI() application that can be installed anywhere without issues.

To use the proxy, you need to configure an application (App) in the DHL Developer Portal. An account in the DHL Developer Portal is required for this.

## Limitations

Currently, only **CreateShipmentDDRequest** messages are processed. The products that can be processed are:

-   DHL Paket (SOAP: _EPN_, Rest: _V01PAK_)
-   DHL Paket International (SOAP: _BPI_, Rest: _V53PAK_)
-   DHL Europaket (SOAP: _EPI_, Rest: _V54EPAK_)

The list can be easily expanded by matching the keys from the SOAP message to the keys of the REST API. Additionally, the prefix (procedure + participation) must be added in the .env file.

## Installation

First, clone the repository:

    clone https://github.com/bizrockman/dhl-soap-proxy.git
    cd dhl-soap-proxy

Then copy the file with the environment variables:

    cp .env.template .env

There you set the variables of your DHL App:

    DHL_API_KEY=  
    DHL_API_SECRET=

the business customer number:

    EKP=

and (optional) the business customer login:

    GKP_USER=
    GKP_PASSWORD=

Optional because in the SOAP v1 interface, the login is transmitted via the SOAP message itself. Only if the entry is missing, the values from the .env file are used.

Then install all dependencies:

    pip install -r requirements.txt

After that, the system can be easily started via:

    uvicorn app:app --reload

For productive operation, the application should be operated behind an nginx proxy that enables secure connections via https.

## Contributing

Support for other messages or SOAP versions is welcome.

## License

This repository is licensed under MIT.


# Deutsche Übersetzung
Mit diesem Projekt kannst du deine Anwendungen, die noch die DHL SOAP API nutzt, weiter verwenden und somit Zeit für eine Migration gewinnen.
Im ersten Zuge wurde nur die SOAP API v1 realisiert, die am 31.05.2024 abgeschaltet wird (wurde).

Mit diesem Projekt hast du ein Framework, um auch die SOAP API v2 und die SOAP API v3 weiter nutzbar zu machen.

## Funktionsweise
Es handelt sich hierbei um einen einfachen Proxy, der SOAP Anfragen gegennimmt und diese an die REST API v2.1 der DHL weiterreicht. Die Anwort wird entgegen genommen und dann wieder in eine SOAP Anfrage gekapselt, die der Client zurück erhält.
Der Proxy ist eine einfache FastAPI() Anwendung, die sich ohne Probleme überall installieren lassen lässt.

Um den Proxy zu verwenden, muss du im Entwicklungsportal der DHL eine Anwendung (App) konfigurieren. Dazu ist ein Konto im DHL Entwicklerportal nötig.

## Einschränkungen
Zur Zeit werden nur **CreateShipmentDDRequest** Nachrichten verarbeitet.
Die Produkte die Verarbeitet werden können sind

 - DHL Paket (SOAP: *EPN*, Rest: *V01PAK*)
 - DHL Paket International (SOAP: *BPI*, Rest: *V53PAK*)
 - DHL Europaket (SOAP: *EPI*, Rest: *V54EPAK*)

Die Liste lässt sich einfach erweitern, in dem die Schlüssel aus der SOAP Nachricht auf die Schlüssel der Rest API gematcht werden. Weiter muss dann in der .env der Prefix (Verfahren + Teilnahme) ergänzt werden.

## Installation
Zunächst clonst du das Repository

    clone https://github.com/bizrockman/dhl-soap-proxy.git
    ce dhl-soap-proxy

Danach kopierst du die Datei mit den Umgebungsvariablen

    cp .env.template .env

Dort legst du dann die Variablen deiner DHL App

    DHL_API_KEY=  
    DHL_API_SECRET=

die Geschäftskundennummer

    EKP=

und (optional) den Geschäftskundenlogin an

    GKP_USER=
    GKP_PASSWORD=

Optional deshalb, weil in der SOAP v1 Schnittstelle der Login über die SOAP Nachricht selbst übermittelt wird. Nur wenn der Eintrag fehlen sollte werden die Werte aus der .env Datei herangezogen.

Anschließend werden alle Abhängigkeiten installiert

    pip install -r requirements.txt

Danach kann das System einfach über

    uvicorn app:app --reload

gestartet werden.

Für den produktiven Betrieb sollte die Anwendung hinter einem nginx proxy betrieben werden, der gesicherte Verbindungen über https ermöglicht.

## Contributing
Unterstützung bei anderen Nachrichten oder SOAP Versionen sind gerne gesehen.

## Lizenz
This repository is licensed under MIT
