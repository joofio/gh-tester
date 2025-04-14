import pytest
import requests
from fhirpathpy import evaluate

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
]

BASE_URL = ["https://gravitate-health.lst.tfo.upm.es/"]


# Reusable evaluation logic (from log_result)
def evaluate_result(status_code, warnings):
    if status_code == 200 and not warnings:
        return 0
    elif status_code != 200:
        return 1
    elif (
        status_code == 200
        and "preprocessingWarnings" in warnings
        and warnings["preprocessingWarnings"]
    ):
        return 2
    elif (
        status_code == 200
        and "lensesWarnings" in warnings
        and warnings["lensesWarnings"]
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


@pytest.mark.parametrize("persona", PATIENT_IDS)
@pytest.mark.parametrize("base_url", BASE_URL)
def test_ips_identifier_and_check_medication(persona, base_url):
    """Test API responses for multiple endpoints."""

    patresp_body = {
        "resourceType": "Parameters",
        "id": "example",
        "parameter": [{"name": "identifier", "valueIdentifier": {"value": persona}}],
    }
    patresp = requests.post(
        base_url + "ips/api/fhir/Patient/$summary", json=patresp_body
    )
    ips = patresp.json()
    medication_codes = parse_ips_med(ips)
    # print(medication_codes)
    for medication in medication_codes:
        listresp = requests.get(
            base_url + "epi/api/fhir/List?subject.identifier=39.955"
        )
        list = listresp.json()
        # print(list)
        bundles = get_bundles_raw(list)

    assert len(medication) > 0, f"No medication data found for persona {persona}"


@pytest.mark.parametrize("base_url", BASE_URL)
def test_check_bundles_in_list(base_url):
    all_checked = []
    list_member_found = []

    bundles_url = f"{base_url}epi/api/fhir/Bundle"
    next_url = bundles_url

    while next_url:
        response = requests.get(next_url)
        assert (
            response.status_code == 200
        ), f"Failed to fetch bundles: {response.status_code}"

        data = response.json()

        for entry in data.get("entry", []):
            bid = entry["resource"]["id"]

            # Skip bundles in the whitelist
            if bid in ENHANCED_WHITE_LIST:
                continue

            # Mark this bundle as checked
            all_checked.append(bid)

            list_check_url = f"{base_url}epi/api/fhir/List?item={bid}"
            list_response = requests.get(list_check_url)
            assert (
                list_response.status_code == 200
            ), f"Failed List check for {bid}: {list_response.status_code}"

            total = list_response.json().get("total", 0)

            # Track which bundles are missing from the List
            if total > 0:
                list_member_found.append((bid, True))
            else:
                list_member_found.append((bid, False))

        # Follow pagination
        next_url = None
        for link in data.get("link", []):
            if link["relation"] == "next":
                next_url = link["url"]
                break

    # ✅ Final assertion: at least some bundles must be checked
    assert len(all_checked) > 0, "No bundles were processed"

    # ✅ Final assertion: all checked bundles should be in a List
    not_found = [bid for bid, found in list_member_found if not found]
    assert len(not_found) == 0, f"Bundles not found in List: {not_found}"


# 2025-01-16T09:44:37.410Z  INFO 1 --- [nio-8080-exec-4] fhirtest.access                          : Path[/fhir] Source[] Operation[search-type  List] UA[Dart/3.5 (dart:io)] Params[?subject.identifier=39.955] ResponseEncoding[JSON] Operation[search-type  List] UA[Dart/3.5 (dart:io)] Params[?subject.identifier=39.955] ResponseEncoding[JSON]


@pytest.mark.parametrize("bundles", BUNDLES)
@pytest.mark.parametrize("patient_ids", PATIENT_IDS)
@pytest.mark.parametrize("base_url", BASE_URL)
def test_all_prpcessor_with_post_data(bundles, patient_ids, base_url):
    print(base_url, patient_ids, bundles)
    bundleresp = requests.get(base_url + "epi/api/fhir/Bundle/" + bundles["id"])
    bundle = bundleresp.json()
    patresp_body = {
        "resourceType": "Parameters",
        "id": "example",
        "parameter": [
            {"name": "identifier", "valueIdentifier": {"value": patient_ids}}
        ],
    }
    print(patresp_body)
    patresp = requests.post(
        base_url + "ips/api/fhir/Patient/$summary", json=patresp_body
    )
    assert patresp.status_code == 200

    ips = patresp.json()
    #  print(ips)
    body = {"epi": bundle, "ips": ips}
    WEBSITE_URL = (
        base_url
        + "focusing/focus?preprocessors=preprocessing-service-mvp2&preprocessors=preprocessing-service-manual"
    )

    focusresp = requests.post(WEBSITE_URL, json=body)
    assert focusresp.status_code == 200

    warnings = eval(focusresp.headers.get("gh-focusing-warnings", "{}"))
    value = evaluate_result(focusresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]
    # status_code, warnings = check_website_status(WEBSITE_URL, body)


@pytest.mark.parametrize("bundles", BUNDLES)
@pytest.mark.parametrize("patient_ids", PATIENT_IDS)
@pytest.mark.parametrize("lenses", LENSES)
@pytest.mark.parametrize("base_url", BASE_URL)
def test_lenses_foralreadypreprocess_data(bundles, lenses, patient_ids, base_url):
    WEBSITE_URL = (
        base_url
        + "focusing/focus/"
        + bundles["id"]
        + "?preprocessors=preprocessing-service-manual&patientIdentifier="
        + patient_ids
        + "&lenses="
        + lenses
    )
    print(WEBSITE_URL)
    bundleresp = requests.post(WEBSITE_URL)

    # WEBSITE_URL = WEBSITE_DATA["url"]
    #  WEBSITE_DESC = WEBSITE_DATA["desc"]
    # status_code, warnings = check_website_status(WEBSITE_URL)
    assert bundleresp.status_code == 200

    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]


@pytest.mark.parametrize("bundles", BUNDLES)
@pytest.mark.parametrize("patient_ids", PATIENT_IDS)
@pytest.mark.parametrize("base_url", BASE_URL)
def test_all_lenses_data(bundles, patient_ids, base_url):
    WEBSITE_URL = (
        base_url
        + "focusing/focus/"
        + bundles["id"]
        + "?preprocessors=preprocessing-service-manual&patientIdentifier="
        + patient_ids
    )
    print(WEBSITE_URL)
    bundleresp = requests.post(WEBSITE_URL)

    assert bundleresp.status_code == 200

    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]


@pytest.mark.parametrize("bundles", BUNDLES)
@pytest.mark.parametrize("patient_ids", PATIENT_IDS)
@pytest.mark.parametrize("base_url", BASE_URL)
def test_all_preprocess_data(bundles, patient_ids, base_url):
    WEBSITE_URL = (
        base_url
        + "focusing/focus/"
        + bundles["id"]
        + "?preprocessors=preprocessing-service-mvp2&preprocessors=preprocessing-service-manual&patientIdentifier="
        + patient_ids
    )
    print(WEBSITE_URL)
    # WEBSITE_URL = WEBSITE_DATA["url"]
    #  WEBSITE_DESC = WEBSITE_DATA["desc"]
    print(WEBSITE_URL)
    bundleresp = requests.post(WEBSITE_URL)

    assert bundleresp.status_code == 200

    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]
