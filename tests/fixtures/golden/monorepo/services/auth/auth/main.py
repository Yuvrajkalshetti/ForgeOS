from shared.util import now_iso


def login_event(user: str) -> str:
    return f"{user}@{now_iso()}"
