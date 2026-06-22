def now_iso() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat()
