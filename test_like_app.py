import pytest
import requests
from fhirpathpy import evaluate

API_IPS_URL = "https://gravitate-health.lst.tfo.upm.es/ips/api/fhir"
API_EPI_URL = "https://gravitate-health.lst.tfo.upm.es/epi/api/fhir"

PERSONAS_IDS = [
    "alicia-1",
    "Cecilia-1",
    "Pedro-1",
]


def parse_ips_med(ips):
    """
    Parses the IPS to get the medication list
    """
    medication = []
    # print(ips)
    result = evaluate(
        ips, "Bundle.entry.where(resource.resourceType=='MedicationStatement')", []
    )
    # print(result)
    for r in result:
        med_ref = r["resource"]["medicationReference"]["reference"]
        # print(med_ref)
        med_id = med_ref.split("/")[-1]
        med = evaluate(ips, "Bundle.entry.where(resource.id=='" + med_id + "')", [])
        # print("result", med)
        med_identifier = med[0]["resource"]["code"]["coding"][0]["code"]
        med_name = med[0]["resource"]["code"]["coding"][0]["display"]

        medication.append(
            {"code": med_identifier, "name": med_name}
        )  # get online first
    print(medication)
    return medication


def get_bundles_raw(list):
    actual_list = evaluate(
        list, "Bundle.entry.where(resource.resourceType == 'List')", []
    )

    print(actual_list)
    bundles_raw = evaluate(list, "List.entry.where(flag.coding[0].code=='01')", [])
    print(bundles_raw)
    return bundles_raw


@pytest.mark.parametrize("persona", PERSONAS_IDS)
def test_api_status(persona):
    """Test API responses for multiple endpoints."""

    patresp_body = {
        "resourceType": "Parameters",
        "id": "example",
        "parameter": [{"name": "identifier", "valueIdentifier": {"value": persona}}],
    }
    patresp = requests.post(API_IPS_URL + "/Patient/$summary", json=patresp_body)
    ips = patresp.json()
    medication_codes = parse_ips_med(ips)
    print(medication_codes)
    for medication in medication_codes:
        listresp = requests.get(API_EPI_URL + "/List?subject.identifier=39.955")
        list = listresp.json()
        # print(list)
        bundles = get_bundles_raw(list)

    assert len(medication) > 0, f"No medication data found for persona {persona}"


# 2025-01-16T09:44:37.410Z  INFO 1 --- [nio-8080-exec-4] fhirtest.access                          : Path[/fhir] Source[] Operation[search-type  List] UA[Dart/3.5 (dart:io)] Params[?subject.identifier=39.955] ResponseEncoding[JSON] Operation[search-type  List] UA[Dart/3.5 (dart:io)] Params[?subject.identifier=39.955] ResponseEncoding[JSON]
