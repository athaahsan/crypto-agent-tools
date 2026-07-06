from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BINANCE_BASE_URL = "https://data-api.binance.vision"
FEAR_GREED_URL = "https://api.alternative.me/fng/"
RSS2JSON_URL = "https://api.rss2json.com/v1/api.json"
COINTELEGRAPH_RSS_URL = "https://cointelegraph.com/rss"


def fetch_ohlcv(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    base_url: str = BINANCE_BASE_URL,
    timeout: int = 20,
) -> list[dict[str, Any]]:
    """Fetch OHLCV candles from Binance public market data."""
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit,
    }
    data = _get_json(f"{base_url}/api/v3/klines", params=params, timeout=timeout)

    if not isinstance(data, list):
        raise RuntimeError(f"Binance OHLCV response was not a list: {data}")

    candles = []
    for item in data:
        candles.append(
            {
                "timestamp": int(item[0]),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
                "close_time": int(item[6]),
            }
        )

    return candles


def fetch_fear_greed_index(
    limit: int = 30,
    date_format: str | None = None,
    timeout: int = 20,
) -> list[dict[str, Any]]:
    """Fetch crypto Fear & Greed Index values from alternative.me."""
    params = {
        "limit": limit,
        "format": "json",
    }
    if date_format:
        params["date_format"] = date_format

    data = _get_json(FEAR_GREED_URL, params=params, timeout=timeout)
    rows = data.get("data") if isinstance(data, dict) else None

    if not isinstance(rows, list):
        raise RuntimeError(f"Fear & Greed response was not valid: {data}")

    values = [
        {
            "value": int(row["value"]),
            "classification": row["value_classification"],
            "timestamp": _parse_timestamp(row["timestamp"], date_format=date_format),
            "time_until_update": _optional_int(row.get("time_until_update")),
        }
        for row in rows
    ]
    values.sort(key=lambda row: row["timestamp"])
    return values


def fetch_crypto_news(
    limit: int = 10,
    rss_url: str = COINTELEGRAPH_RSS_URL,
    timeout: int = 20,
) -> list[dict[str, Any]]:
    """Fetch crypto news from an RSS feed through rss2json."""
    params = {"rss_url": rss_url}
    data = _get_json(RSS2JSON_URL, params=params, timeout=timeout)

    if data.get("status") != "ok" or not isinstance(data.get("items"), list):
        raise RuntimeError(f"News response was not valid: {data}")

    articles = []
    for item in data["items"][:limit]:
        articles.append(
            {
                "title": item.get("title"),
                "url": item.get("link"),
                "thumb": item.get("thumbnail") or _nested_get(item, "enclosure", "link"),
                "author": item.get("author") or "Cointelegraph",
                "created_at": _parse_pub_date(item.get("pubDate")),
            }
        )

    return articles


def _get_json(url: str, params: dict[str, Any], timeout: int) -> Any:
    full_url = f"{url}?{urlencode(params)}"
    request = Request(full_url, headers={"User-Agent": "crypto-agent-tools/0.1"})

    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _nested_get(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _parse_pub_date(value: str | None) -> int | None:
    if not value:
        return None

    from email.utils import parsedate_to_datetime

    try:
        return int(parsedate_to_datetime(value).timestamp())
    except (TypeError, ValueError):
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            parsed = datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return int(parsed.timestamp())
        except ValueError:
            continue

    return None


def _parse_timestamp(value: Any, date_format: str | None = None) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        pass

    if not isinstance(value, str):
        raise ValueError(f"Invalid timestamp value: {value}")

    formats = []
    if date_format == "us":
        formats.append("%m-%d-%Y")
    elif date_format in {"world", "cn"}:
        formats.append("%d-%m-%Y")

    formats.extend(["%m-%d-%Y", "%d-%m-%Y", "%Y-%m-%d"])

    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            return int(parsed.timestamp())
        except ValueError:
            continue

    raise ValueError(f"Invalid timestamp value: {value}")
