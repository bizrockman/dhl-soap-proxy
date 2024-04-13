import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


def pretty_print_xml(file_path):
    # Parse die XML-Datei
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Konvertiere den ElementTree zurück in einen String und nutze minidom für das Pretty Printing
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_string = reparsed.toprettyxml(indent="  ")

    # Speichere die hübsch formatierte XML in einer neuen Datei
    with open(file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(pretty_string)

def extrahiere_soap_body_elemente(dateipfad):
    start_tag = "<SOAP-ENV:Body>"
    end_tag = "</SOAP-ENV:Body>"

    start_tag_regexp = r"<([^:\s>]*:)?Body>"
    end_tag_regexp = r"</([^:\s>]*:)?Body>"

    erstes_element_regexp = r"<([^>\s:]+:[^>\s]+)"
    methods_dict = {}

    with open(dateipfad, 'r', encoding='utf-8') as datei:
        auszug = ""
        innerhalb_soap_body = False
        for zeile in datei:
            start_tag_match = re.search(start_tag_regexp, zeile)
            #if start_tag in zeile and not innerhalb_soap_body:
            if start_tag_match and not innerhalb_soap_body:
                innerhalb_soap_body = True
                #zeile = zeile.split(start_tag)[-1]  # Entfernt den Teil der Zeile vor dem Start-Tag
                zeile = zeile[start_tag_match.end():]

            # Wenn wir uns innerhalb eines SOAP-Body befinden
            if innerhalb_soap_body:
                # Überprüfen, ob das End-Tag in der aktuellen Zeile ist
                end_tag_match = re.search(end_tag_regexp, zeile)
                # if end_tag in zeile:
                if end_tag_match:
                    #auszug += zeile.split(end_tag)[0]  # Fügt den Inhalt vor dem End-Tag zum Auszug hinzu
                    auszug += zeile[:end_tag_match.start()]

                    # Extrahieren des ersten Elements im Auszug
                    erstes_element_match = re.search(erstes_element_regexp, auszug)
                    if erstes_element_match:
                        element_name = erstes_element_match.group(1)
                        if element_name in methods_dict:
                            methods_dict[element_name] += 1
                        else:
                            methods_dict[element_name] = 1

                    auszug = ""  # Setzt den Auszug für das nächste Element zurück
                    innerhalb_soap_body = False  # Verlässt den SOAP-Body Zustand

                else:
                    auszug += zeile  # Fügt die gesamte Zeile zum Auszug hinzu, da kein End-Tag gefunden wurde

    return methods_dict


def extrahiere_soap_messages(dateipfad):
    start_tag = "<SOAP-ENV:Body>"
    end_tag = "</SOAP-ENV:Body>"

    start_tag_regexp = r"<([^:\s>]*:)?Envelope"
    end_tag_regexp = r"</([^:\s>]*:)?Envelope>"

    erstes_element_regexp = r"<([^>\s:]+:[^>\s]+)"
    methods_dict = {}
    max_hits = 100000
    hits = 0
    is_request = False
    soap_request_counter = 0

    with open(dateipfad, 'r', encoding='utf-8') as datei:
        auszug = ""
        innerhalb_soap_body = False
        for zeile in datei:
            if 'REQUEST' in zeile:
                is_request = True
                soap_request_counter += 1
            start_tag_match = re.search(start_tag_regexp, zeile)
            #if start_tag in zeile and not innerhalb_soap_body:
            if start_tag_match and not innerhalb_soap_body:

                innerhalb_soap_body = True
                #zeile = zeile.split(start_tag)[-1]  # Entfernt den Teil der Zeile vor dem Start-Tag
                zeile = zeile[start_tag_match.start():]

            # Wenn wir uns innerhalb eines SOAP-Body befinden
            if innerhalb_soap_body:
                # Überprüfen, ob das End-Tag in der aktuellen Zeile ist
                end_tag_match = re.search(end_tag_regexp, zeile)
                # if end_tag in zeile:
                if end_tag_match:
                    #auszug += zeile.split(end_tag)[0]  # Fügt den Inhalt vor dem End-Tag zum Auszug hinzu
                    auszug += zeile[:end_tag_match.end()]

                    # Extrahieren des ersten Elements im Auszug
                    erstes_element_match = re.search(erstes_element_regexp, auszug)
                    if erstes_element_match:
                        element_name = erstes_element_match.group(1)
                        if element_name in methods_dict:
                            methods_dict[element_name] += 1
                        else:
                            methods_dict[element_name] = 1

                    if hits > max_hits:
                        break
                    else:
                        if is_request:
                            print("REQUEST")
                            fileprefix = "request"
                        else:
                            print("RESPONSE")
                            fileprefix = "response"

                        print(auszug)
                        print("-"*50)
                        # write auszug to xml file with name soap_request- <counter>.xml
                        with open(f'samples/soap-{fileprefix}-{soap_request_counter}.xml', 'w', encoding='utf-8') as f:
                            f.write(auszug)

                        hits += 1

                    auszug = ""  # Setzt den Auszug für das nächste Element zurück
                    is_request = False
                    innerhalb_soap_body = False  # Verlässt den SOAP-Body Zustand

                else:
                    auszug += zeile  # Fügt die gesamte Zeile zum Auszug hinzu, da kein End-Tag gefunden wurde

    return methods_dict

# Anwenden der Funktion
log_path = 'res/intraship.log'
#methods_dict = extrahiere_soap_body_elemente(log_path)
methods_dict = extrahiere_soap_messages(log_path)
print(methods_dict)
