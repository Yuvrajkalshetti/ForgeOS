from shared.util import now_iso


def invoice_stamp(invoice_id: str) -> str:
    return f"{invoice_id}:{now_iso()}"
