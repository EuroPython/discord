"""Mock Pretix HTTP Server."""

import argparse
import http.server
import json
import logging
import socketserver
import sys
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DESCRIPTION = """\
Mock Pretix HTTP Server with the following orders:

Order 'AAAAA' (paid)
- Business Combined Ticket for 'Jane Doe'
- Business Tutorial Ticket for 'John Doe'
- Childcare

Order 'BBB22' (paid)
- Volunteer Ticket for 'Minta János'
- Speaker Ticket for 'Minta Kata'
- T-Shirt

Order 'CCC33' (paid)
- Personal Remote Ticket for 'Martina Mustermann'

Order 'DDDD44' (paid)
- Sponsor Ticket for Seán Ó Rudaí
- T-Shirt

Order 'EEE55' (payment pending)
- Personal Late Conference Ticket for 'Numerius Negidius'
"""

PRETIX_ITEMS = {
    "count": 10,
    "next": None,
    "results": [
        {
            "id": 1,
            "name": {"en": "Business"},
            "variations": [
                {"id": 101, "value": {"en": "Conference"}},
                {"id": 102, "value": {"en": "Tutorials"}},
                {"id": 103, "value": {"en": "Combined (Conference + Tutorials)"}},
                {"id": 104, "value": {"en": "Late Conference"}},
                {"id": 105, "value": {"en": "Late Combined"}},
            ],
        },
        {
            "id": 2,
            "name": {"en": "Personal"},
            "variations": [
                {"id": 201, "value": {"en": "Conference"}},
                {"id": 202, "value": {"en": "Tutorials"}},
                {"id": 203, "value": {"en": "Combined (Conference + Tutorials)"}},
                {"id": 204, "value": {"en": "Late Conference"}},
                {"id": 205, "value": {"en": "Late Combined"}},
            ],
        },
        {
            "id": 3,
            "name": {"en": "Education"},
            "variations": [
                {"id": 301, "value": {"en": "Conference"}},
                {"id": 302, "value": {"en": "Tutorials"}},
                {"id": 303, "value": {"en": "Combined (Conference + Tutorials)"}},
            ],
        },
        {
            "id": 4,
            "name": {"en": "Community Contributors"},
            "variations": [
                {"id": 401, "value": {"en": "Volunteer"}},
                {"id": 402, "value": {"en": "Python Community Organiser"}},
            ],
        },
        {
            "id": 5,
            "name": {"en": "Childcare (Free for children aged 18 months and older)"},
            "variations": [],
        },
        {
            "id": 6,
            "name": {"en": "Presenter"},
            "variations": [
                {"id": 601, "value": {"en": "Speaker"}},
                {"id": 602, "value": {"en": "Tutorial & Workshop Presenter"}},
                {"id": 603, "value": {"en": "Keynote Presenter"}},
            ],
        },
        {"id": 7, "name": {"en": "T-shirt (free)"}, "variations": []},
        {"id": 8, "name": {"en": "Grant ticket"}, "variations": []},
        {"id": 9, "name": {"en": "Sponsor Conference Pass"}, "variations": []},
        {
            "id": 10,
            "name": {"en": "Remote Participation Ticket"},
            "variations": [
                {"id": 1001, "value": {"en": "Business Remote"}},
                {"id": 1002, "value": {"en": "Personal Remote"}},
            ],
        },
    ],
}
PRETIX_ORDERS = {
    "count": 5,
    "next": None,
    "results": [
        {
            "code": "AAA11",
            "status": "p",
            "positions": [
                {"order": "AAA11", "item": 1, "variation": 103, "attendee_name": "Jane Doe"},
                {"order": "AAA11", "item": 1, "variation": 102, "attendee_name": "John Doe"},
                {"order": "AAA11", "item": 5, "variation": None, "attendee_name": None},
            ],
        },
        {
            "code": "BBB22",
            "status": "p",
            "positions": [
                {"order": "BBB22", "item": 4, "variation": 401, "attendee_name": "Minta János"},
                {"order": "BBB22", "item": 6, "variation": 601, "attendee_name": "Minta Kata"},
                {"order": "BBB22", "item": 7, "variation": None, "attendee_name": None},
            ],
        },
        {
            "code": "CCC33",
            "status": "p",
            "positions": [
                {
                    "order": "CCC33",
                    "item": 10,
                    "variation": 1002,
                    "attendee_name": "Martina Mustermann",
                }
            ],
        },
        {
            "code": "DDD44",
            "status": "p",
            "positions": [
                {"order": "DDD44", "item": 9, "variation": None, "attendee_name": "Seán Ó Rudaí"},
                {"order": "DDD44", "item": 7, "variation": None, "attendee_name": None},
            ],
        },
        {
            "code": "EEE55",
            "status": "n",
            "positions": [
                {
                    "order": "EEE55",
                    "item": 2,
                    "variation": 204,
                    "attendee_name": "Numerius Negidius",
                }
            ],
        },
    ],
}


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (function name should be lowercase)
        """Handle GET requests."""
        path = urlparse(self.path).path  # strip query parameters

        path_to_response_body = {
            "/items.json": PRETIX_ITEMS,
            "/orders.json": PRETIX_ORDERS,
        }
        response_body = path_to_response_body.get(path)
        if response_body is None:
            self.send_error(http.HTTPStatus.NOT_FOUND, "Not Found")
            logger.warning(f"GET {path} - 404")
        else:
            self.send_response(http.HTTPStatus.OK, "OK")
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(response_body).encode("utf-8"))
            logger.info(f"GET {path} - 200")

    def log_message(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401 (typing.Any)
        pass  # disable built-in logging


def main(args: list[str] | None) -> None:
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")

    args = parser.parse_args(args)

    with socketserver.ThreadingTCPServer(("localhost", args.port), RequestHandler) as httpd:
        logger.info("Serving at localhost:%d", args.port)
        httpd.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main(sys.argv[1:])
