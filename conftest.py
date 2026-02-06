import json
import os

import pytest
from fhirpathpy import evaluate


def pytest_addoption(parser):
    parser
    parser.addoption(
        "--base-url",
        action="store",
        default="https://gravitate-health.lst.tfo.upm.es/",
        help="Base URL for API requests (default: https://gravitate-health.lst.tfo.upm.es/",
    )


# Fixture to access the command-line argument
@pytest.fixture(scope="session")
def base_url(request):
    return request.config.getoption("--base-url")


PATIENT_IDS = [
    "alicia-1",
    "Cecilia-1",
    "Pedro-1",
    "helen-1",
    "maria-1",
    "0101010101",
    "ips-1",
    "ips-2",
    "ips-3",
    "ips-4",
]
LENSES = [
    "lens-selector-mvp2_HIV",
    "lens-selector-mvp2_allergy",
    "lens-selector-mvp2_diabetes",
    "lens-selector-mvp2_interaction",
    "lens-selector-mvp2_intolerance",
    "lens-selector-mvp2_pregnancy",
]
PREPROCBUNDLES = {
    "processedbundlekarveabik": "biktarvy-en",
    "bundleprocessed-es-b44cce291e466626afa836fffe72c350": "biktarvy-es",
    "bundleprocessed-pt-b44cce291e466626afa836fffe72c350": "biktarvy-pt",
    "processedbundlekarveacalcium": "calcium_pt",
    "processedbundledovato-en": "dovato-en",
    "processedbundledovato-es": "dovato-es",
    "processedbundleflucelvax": "flucelvax-en",
    "processedbundleflucelvaxES": "flucelvax-es",
    "processedbundlehypericum": "hypericum-es",
    "bundle-ibu-proc": "ibuprofen-en",
    "Processedbundlekarvea": "karvea-en",
    "bundle-processed-pt-2d49ae46735143c1323423b7aea24165": "karvea-pt",
    "bundle-met-proc": "metformin-en",
    "bundle-novo-proc": "novorapid-en",
    "bundlepackageleaflet-es-proc-2f37d696067eeb6daf1111cfc3272672": "tegretrol-es",
    "bundlepackageleaflet-es-proc-4fab126d28f65a1084e7b50a23200363": "xenical-es",
}

BUNDLES = [
    {
        "id": "bundlepackageleaflet-es-94a96e39cfdcd8b378d12dd4063065f9",
        "name": "biktarvy-es",
    },
    {
        "id": "bundlepackageleaflet-en-94a96e39cfdcd8b378d12dd4063065f9",
        "name": "biktarvy-en",
    },
    {
        "id": "bundlepackageleaflet-es-925dad38f0afbba36223a82b3a766438",
        "name": "calcio-es",
    },
    {
        "id": "bundlepackageleaflet-es-2f37d696067eeb6daf1111cfc3272672",
        "name": "tegretol-es",
    },
    {
        "id": "bundlepackageleaflet-en-2f37d696067eeb6daf1111cfc3272672",
        "name": "tegretol-en",
    },
    {
        "id": "bundlepackageleaflet-es-4fab126d28f65a1084e7b50a23200363",
        "name": "xenical-es",
    },
    {
        "id": "bundlepackageleaflet-en-4fab126d28f65a1084e7b50a23200363",
        "name": "xenical-en",
    },
    {
        "id": "bundlepackageleaflet-es-29436a85dac3ea374adb3fa64cfd2578",
        "name": "hypericum-es",
    },
    {
        "id": "bundlepackageleaflet-es-04c9bd6fb89d38b2d83eced2460c4dc1",
        "name": "flucelvax-es",
    },
    {
        "id": "bundlepackageleaflet-en-04c9bd6fb89d38b2d83eced2460c4dc1",
        "name": "flucelvax-en",
    },
    {
        "id": "bundlepackageleaflet-es-49178f16170ee8a6bc2a4361c1748d5f",
        "name": "dovato-es",
    },
    {
        "id": "bundlepackageleaflet-en-49178f16170ee8a6bc2a4361c1748d5f",
        "name": "dovato-en",
    },
    {
        "id": "bundlepackageleaflet-es-e762a2f54b0b24fca4744b1bb7524a5b",
        "name": "mirtazapine-es",
    },
    {
        "id": "bundlepackageleaflet-es-da0fc2395ce219262dfd4f0c9a9f72e1",
        "name": "blaston-es",
    },
]


ENHANCED_WHITE_LIST = [
    "enhanced-bundlebik-alicia",
    "enhanced-bundlekarveacalcium-alicia",
    "enchanced-bundledovato-es",
    "enchanced-bundledovato-en",
    "enhanced-bundleflucelvax-alicia",
    "enhanced-bundlehypericum-alicia",
    "enhancedbundlekarvea-alicia",
    "enhancedddbundlekarvea",
    "enhanced-bundlebik-pedro",
    "enhanced-bundlekarveacalcium-pedro",
    "enchanced-bundledovato-pedro-en",
    "enchanced-bundledovato-pedro-es",
    "enhanced-bundleflucelvax-pedro",
    "enhanced-bundlehypericum-pedro",
    "enhancedbundlekarveaP",
    "pedro-dimension-collection",
    "persona-dimension-collection",
    "bundlepackageleafletxyntha",
    "bundlepackageleaflet-xeljanz",
    "bundlejpiherceptin150",
    "bundlejpisimvastatin20",
    "bundlejpicarbamazepine200",
    "bundleproductmonographxyntha",
    "bundle-ibrance75-100-125",
    "bundlepackageleaflet-379d610f9c96d541562699215b0864127",
    "bundlepackageleaflet-378d610f9c96d541562699215b0864126",
    "DPHARM123",
    "FK40274",
    "FK40703",
    "FK37796",
    "FK40963",
    "FK39664",
]


# Reusable evaluation logic (from log_result)
def _has_nonempty_warnings(value):
    if not value:
        return False
    if isinstance(value, dict):
        return any(_has_nonempty_warnings(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_has_nonempty_warnings(v) for v in value)
    return True


def evaluate_result(status_code, warnings):
    if status_code == 200 and not _has_nonempty_warnings(warnings):
        return 0
    elif status_code != 200:
        return 1
    elif (
        status_code == 200
        and "preprocessingWarnings" in warnings
        and _has_nonempty_warnings(warnings["preprocessingWarnings"])
    ):
        return 2
    elif (
        status_code == 200
        and "lensesWarnings" in warnings
        and _has_nonempty_warnings(warnings["lensesWarnings"])
    ):
        return 3
    else:
        return 4


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
    # print(medication)
    return medication


def get_bundles_raw(list):
    actual_list = evaluate(
        list, "Bundle.entry.where(resource.resourceType == 'List')", []
    )

    #  print(actual_list)
    bundles_raw = evaluate(list, "List.entry.where(flag.coding[0].code=='01')", [])
    # print(bundles_raw)
    return bundles_raw


def load_local_data(case_id: int):
    base_path = os.path.join(os.path.dirname(__file__), "data")

    ips_path = os.path.join(base_path, f"{case_id}_ips.json")
    epi_path = os.path.join(base_path, f"{case_id}_epi.json")

    try:
        with open(ips_path, encoding="utf-8") as f:
            ips = json.load(f)
        with open(epi_path, encoding="utf-8") as f:
            epi = json.load(f)
        return ips, epi
    except FileNotFoundError:
        return None, None
