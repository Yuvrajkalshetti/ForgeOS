import json

from pkg_b.helper import normalize


def encode(value: dict) -> str:
    return json.dumps(normalize(value))
