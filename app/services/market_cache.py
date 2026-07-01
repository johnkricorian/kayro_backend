from datetime import datetime, timedelta

_CACHE: dict = {}

TTL = timedelta(minutes=15)


def get(key: str):
    item = _CACHE.get(key)

    if item is None:
        return None

    expires_at, value = item

    if datetime.now() > expires_at:
        del _CACHE[key]
        return None

    return value


def set(key: str, value):
    _CACHE[key] = (
        datetime.now() + TTL,
        value
    )


def clear():
    _CACHE.clear()
