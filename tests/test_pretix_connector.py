import json
from http import HTTPStatus
from pathlib import Path
from unittest import mock

from EuroPythonBot.configuration import Config
from EuroPythonBot.helpers.pretix_connector import get_pretix_checkinlists_data

config = Config()


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            return self.status_code

    if args[0] == f"{config.PRETIX_BASE_URL}/checkinlists/{config.CHECKINLIST_ID}/positions":
        with open(Path("tests", "mock_pretix_checkinglists_list_positions.json")) as json_file:
            mock_response = json.load(json_file)
        return MockResponse(json_data=mock_response, status_code=HTTPStatus.OK)

    return MockResponse(None, HTTPStatus.NOT_FOUND)


@mock.patch("requests.get", side_effect=mocked_requests_get)
def test_get_pretix_checkinlists_data(mocked_requests_get):
    expected_response = {
        "90LKW-dogtbd": "Personal-Conference",
        "M09CT-order2dog": "Business-Conference",
        "M09CT-order3dog": "Business-Conference",
        "M09CT-order4dog": "Business-Conference",
        "M09CT-order5dog": "Business-Conference",
        "M09CT-order6dog": "Business-Conference",
        "C0MV7-raquelindividual": "Business-Conference",
        "G0CFM-raquelindividual": "Business-Conference",
        "90LKW-tbdtbd": "Business-Conference",
        "RCZN9-todoggodot": "Presenter-Speaker",
        "30QNE-todogtalksnoemu": "Presenter-Speaker",
    }

    assert get_pretix_checkinlists_data() == expected_response
