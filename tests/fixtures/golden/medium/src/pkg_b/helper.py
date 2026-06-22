import httpx  # external dependency


def normalize(value: dict) -> dict:
    return {k: v for k, v in sorted(value.items())}


def fetch(url: str) -> int:
    return httpx.get(url).status_code
