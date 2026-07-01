from datetime import datetime, timedelta

_CACHE: dict[str, tuple[datetime, list[dict]]] = {}

TTL = timedelta(minutes=10)


def get(sector: str):

    item = _CACHE.get(sector.lower())

    if item is None:
        return None

    expires_at, value = item

    if datetime.now() > expires_at:
        del _CACHE[sector.lower()]
        return None

    return value


def set(
    sector: str,
    value: list[dict]
):
    _CACHE[sector.lower()] = (
        datetime.now() + TTL,
        value
    )


def clear():
    _CACHE.clear()
