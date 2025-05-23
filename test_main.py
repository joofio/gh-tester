import json

import pytest
import requests
from conftest import (
    BUNDLES,
    ENHANCED_WHITE_LIST,
    LENSES,
    PATIENT_IDS,
    evaluate_result,
    get_bundles_raw,
    load_local_data,
    parse_ips_med,
)


@pytest.mark.dependency()
def test_environment(base_url):
    url = base_url + "/epi/api/fhir/Bundle/"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except Exception as e:
        pytest.skip(f"❌ Skipping all tests: environment check failed → {e}")

    if response:
        data = response.json()
        assert len(data["entry"]) > 0


@pytest.mark.parametrize("persona", PATIENT_IDS)
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


# @pytest.mark.dependency(depends=["test_environment"])
def test_if_lens_exist(base_url):
    response = requests.get(base_url + "/focusing/lenses")
    data = response.json()

    print(data)
    assert response.status_code == 200, "Expected 200 OK"
    assert "lenses" in data, "'lenses' key missing in response"
    assert len(data["lenses"]) > 0, "Expected at least one lens"


@pytest.mark.dependency(depends=["test_environment"])
@pytest.mark.parametrize("bundles", BUNDLES)
@pytest.mark.parametrize("patient_ids", PATIENT_IDS)
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
    # print(WEBSITE_URL)
    bundleresp = requests.post(WEBSITE_URL)

    assert bundleresp.status_code == 200

    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]


@pytest.mark.dependency(depends=["test_environment"])
@pytest.mark.parametrize("bundles", BUNDLES)
@pytest.mark.parametrize("patient_ids", PATIENT_IDS)
def test_all_prpcessor_with_post_data(bundles, patient_ids, base_url):
    # print(base_url, patient_ids, bundles)
    bundleresp = requests.get(base_url + "epi/api/fhir/Bundle/" + bundles["id"])
    bundle = bundleresp.json()
    patresp_body = {
        "resourceType": "Parameters",
        "id": "example",
        "parameter": [
            {"name": "identifier", "valueIdentifier": {"value": patient_ids}}
        ],
    }
    # print(patresp_body)
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
    print(WEBSITE_URL)

    focusresp = requests.post(WEBSITE_URL, json=body)
    assert focusresp.status_code == 200

    warnings = eval(focusresp.headers.get("gh-focusing-warnings", "{}"))
    value = evaluate_result(focusresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]
    # status_code, warnings = check_website_status(WEBSITE_URL, body)


@pytest.mark.dependency(depends=["test_environment"])
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


@pytest.mark.dependency(depends=["test_environment", "test_if_lens_exist"])
@pytest.mark.parametrize("bundles", BUNDLES)
@pytest.mark.parametrize("patient_ids", PATIENT_IDS)
@pytest.mark.parametrize("lenses", LENSES)
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
    #
    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]


@pytest.mark.dependency(depends=["test_environment", "test_if_lens_exist"])
@pytest.mark.parametrize("bundles", BUNDLES)
@pytest.mark.parametrize("patient_ids", PATIENT_IDS)
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


@pytest.mark.dependency(depends=["test_environment", "test_if_lens_exist"])
def test_pregnancy_lens(base_url):
    WEBSITE_URL = (
        base_url
        + "focusing/focus?preprocessors=preprocessing-service-manual&lenses=pregnancy-lens"
    )
    print(WEBSITE_URL)
    ips, epi = load_local_data(1)
    assert ips is not None and epi is not None, "Missing input files for this test case"

    payload = {"ips": ips, "epi": epi}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # print(payload)
    bundleresp = requests.post(WEBSITE_URL, json=payload, headers=headers)

    assert bundleresp.status_code == 200

    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]

    response_text = json.dumps(bundleresp.json())

    # Check for keywords
    assert "pregnancy-lens" in response_text
    assert " highlight " in response_text


# @pytest.mark.dependency(depends=["test_environment", "test_if_lens_exist"])
def test_allergy_lens(base_url):
    WEBSITE_URL = (
        base_url
        + "focusing/focus?preprocessors=preprocessing-service-manual&lenses=allergyintollerance-lens"
    )
    print(WEBSITE_URL)
    ips, epi = load_local_data(2)
    assert ips is not None and epi is not None, "Missing input files for this test case"

    payload = {"ips": ips, "epi": epi}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # print(payload)
    bundleresp = requests.post(WEBSITE_URL, json=payload, headers=headers)

    assert bundleresp.status_code == 200

    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]

    response_text = json.dumps(bundleresp.json())

    # Check for keywords
    assert "allergyintollerance-lens" in response_text
    assert " highlight " in response_text


def test_contact_lens(base_url):
    WEBSITE_URL = (
        base_url
        + "focusing/focus?preprocessors=preprocessing-service-manual&lenses=contact-lens"
    )
    print(WEBSITE_URL)
    ips, epi = load_local_data(3)
    assert ips is not None and epi is not None, "Missing input files for this test case"

    payload = {"ips": ips, "epi": epi}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # print(payload)
    bundleresp = requests.post(WEBSITE_URL, json=payload, headers=headers)

    assert bundleresp.status_code == 200

    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]

    response_text = json.dumps(bundleresp.json())
    print(response_text)
    # Check for keywords
    assert "contact-lens" in response_text
    assert " highlight " in response_text


def test_questionnaire_lens(base_url):
    WEBSITE_URL = (
        base_url
        + "focusing/focus?preprocessors=preprocessing-service-manual&lenses=questionnaire-lens"
    )
    print(WEBSITE_URL)
    ips, epi = load_local_data(4)
    assert ips is not None and epi is not None, "Missing input files for this test case"

    payload = {"ips": ips, "epi": epi}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # print(payload)
    bundleresp = requests.post(WEBSITE_URL, json=payload, headers=headers)

    assert bundleresp.status_code == 200

    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    print(warnings)
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]

    response_text = json.dumps(bundleresp.json())
    print(response_text)

    # Check for keywords
    assert "questionnaire-lens" in response_text
    assert "https://example.org/questionnaire/high-risk" in response_text


def test_doping_lens(base_url):
    WEBSITE_URL = (
        base_url
        + "focusing/focus?preprocessors=preprocessing-service-manual&lenses=doping-lens"
    )
    print(WEBSITE_URL)
    ips, epi = load_local_data(5)
    assert ips is not None and epi is not None, "Missing input files for this test case"

    payload = {"ips": ips, "epi": epi}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # print(payload)
    bundleresp = requests.post(WEBSITE_URL, json=payload, headers=headers)

    assert bundleresp.status_code == 200

    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    print(warnings)
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]

    response_text = json.dumps(bundleresp.json())
    print(response_text)

    # Check for keywords
    assert "doping-lens" in response_text
    assert " highlight " in response_text


def test_indication_lens(base_url):
    WEBSITE_URL = (
        base_url
        + "focusing/focus?preprocessors=preprocessing-service-manual&lenses=indication-lens"
    )
    print(WEBSITE_URL)
    ips, epi = load_local_data(6)
    assert ips is not None and epi is not None, "Missing input files for this test case"

    payload = {"ips": ips, "epi": epi}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # print(payload)
    bundleresp = requests.post(WEBSITE_URL, json=payload, headers=headers)

    assert bundleresp.status_code == 200

    warnings = eval(bundleresp.headers.get("gh-focusing-warnings", "{}"))
    print(warnings)
    value = evaluate_result(bundleresp.status_code, warnings)

    # ✅ Core assertion
    assert value in [0]

    response_text = json.dumps(bundleresp.json())
    print(response_text)

    # Check for keywords
    assert "indication-lens" in response_text
    assert " highlight " in response_text
