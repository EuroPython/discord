import pytest

from registration.ticket import generate_ticket_key


@pytest.mark.parametrize(
    ("name", "result"),
    [
        ("Karel Čapek", "karelcapek"),
        ("Shin Kyung-sook", "shinkyungsook"),
        ("Ch'oe Yun", "choeyun"),
        ("Æmilia Lanyer", "aemilialanyer"),
        ("name@example.com", "nameexamplecom"),
    ],
)
def test_name_normalization(name: str, result: str) -> None:
    key = generate_ticket_key(order="ABC01", name=name)
    assert key == f"ABC01-{result}"
