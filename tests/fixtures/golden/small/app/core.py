from app.utils import slugify


def make_key(title: str) -> str:
    return f"key:{slugify(title)}"
