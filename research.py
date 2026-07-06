from __future__ import annotations

from typing import Any

from indicators import (
    calculate_adx_from_candles,
    calculate_atr_from_candles,
    calculate_bollinger_bands_from_candles,
    calculate_ema_from_candles,
    calculate_macd_from_candles,
    calculate_rsi_from_candles,
)
from market_data import fetch_crypto_news, fetch_fear_greed_index, fetch_ohlcv


def get_market_snapshot(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return _market_snapshot_from_candles(candles, symbol=symbol, interval=interval)


def analyze_trend(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return _trend_from_candles(candles, symbol=symbol, interval=interval)


def analyze_momentum(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return _momentum_from_candles(candles, symbol=symbol, interval=interval)


def analyze_volatility(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return _volatility_from_candles(candles, symbol=symbol, interval=interval)


def find_support_resistance(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return _support_resistance_from_candles(candles, symbol=symbol, interval=interval)


def get_crypto_sentiment(timeout: int = 20) -> dict[str, Any]:
    values = fetch_fear_greed_index(limit=30, timeout=timeout)
    if not values:
        raise ValueError("Fear & Greed response returned no values")

    latest = values[-1]
    previous = values[-2] if len(values) > 1 else None
    previous_value = previous["value"] if previous else None

    return {
        "fear_greed_value": latest["value"],
        "fear_greed_class": latest["classification"],
        "previous_value": previous_value,
        "change": None if previous_value is None else latest["value"] - previous_value,
        "last_7_values": [row["value"] for row in values[-7:]],
    }


def build_market_report(
    symbol: str = "BTCUSDT",
    intervals: list[str] | None = None,
    limit: int = 300,
    timeout: int = 20,
    include_sentiment: bool = True,
    include_news: bool = True,
    news_limit: int = 5,
) -> dict[str, Any]:
    selected_intervals = normalize_intervals(intervals)
    reports = {}

    for interval in selected_intervals:
        candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
        reports[interval] = {
            "snapshot": _market_snapshot_from_candles(candles, symbol=symbol, interval=interval),
            "trend": _trend_from_candles(candles, symbol=symbol, interval=interval),
            "momentum": _momentum_from_candles(candles, symbol=symbol, interval=interval),
            "volatility": _volatility_from_candles(candles, symbol=symbol, interval=interval),
            "support_resistance": _support_resistance_from_candles(candles, symbol=symbol, interval=interval),
        }

    sentiment = get_crypto_sentiment(timeout=timeout) if include_sentiment else None
    news = fetch_crypto_news(limit=news_limit, timeout=timeout) if include_news else []

    return {
        "symbol": symbol.upper(),
        "intervals": selected_intervals,
        "limit": limit,
        "sentiment": sentiment,
        "news": news,
        "overall_summary": _overall_summary(reports, sentiment),
        "reports": reports,
    }


def normalize_intervals(intervals: list[str] | None) -> list[str]:
    if intervals is None:
        return ["1d", "4h", "1h"]

    normalized = []
    for item in intervals:
        for interval in item.split(","):
            cleaned = interval.strip()
            if cleaned:
                if cleaned.isdigit():
                    cleaned = f"{cleaned}d"
                normalized.append(cleaned)

    if not normalized:
        raise ValueError("At least one interval is required")

    return normalized


def _market_snapshot_from_candles(
    candles: list[dict[str, Any]],
    symbol: str,
    interval: str,
) -> dict[str, Any]:
    _require_candles(candles)
    first = candles[0]
    latest = candles[-1]
    latest_close = float(latest["close"])
    first_open = float(first["open"])

    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "candles_analyzed": len(candles),
        "latest_close": latest_close,
        "latest_open": float(latest["open"]),
        "latest_high": float(latest["high"]),
        "latest_low": float(latest["low"]),
        "latest_volume": float(latest["volume"]),
        "price_change_percent": _percent_change(latest_close, first_open),
        "last_14_closes": [float(candle["close"]) for candle in candles[-14:]],
    }


def _trend_from_candles(
    candles: list[dict[str, Any]],
    symbol: str,
    interval: str,
) -> dict[str, Any]:
    _require_candles(candles)
    latest_close = float(candles[-1]["close"])
    ema_20 = calculate_ema_from_candles(candles, symbol=symbol, interval=interval, length=20)["latest"]
    ema_50 = calculate_ema_from_candles(candles, symbol=symbol, interval=interval, length=50)["latest"]
    ema_100 = calculate_ema_from_candles(candles, symbol=symbol, interval=interval, length=100)["latest"]
    adx_result = calculate_adx_from_candles(candles, symbol=symbol, interval=interval)
    adx_latest = adx_result["latest"]

    price_vs_ema20 = _percent_change(latest_close, ema_20)
    price_vs_ema50 = _percent_change(latest_close, ema_50)
    price_vs_ema100 = _percent_change(latest_close, ema_100)
    ema_alignment = _ema_alignment(ema_20, ema_50, ema_100)
    trend_strength = _trend_strength(adx_latest["adx"])
    trend_direction = _trend_direction(
        latest_close=latest_close,
        ema_20=ema_20,
        ema_50=ema_50,
        ema_100=ema_100,
        ema_alignment=ema_alignment,
        plus_di=adx_latest["plus_di"],
        minus_di=adx_latest["minus_di"],
    )

    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "latest_close": latest_close,
        "ema_20": ema_20,
        "ema_50": ema_50,
        "ema_100": ema_100,
        "price_vs_ema20_percent": price_vs_ema20,
        "price_vs_ema50_percent": price_vs_ema50,
        "price_vs_ema100_percent": price_vs_ema100,
        "ema_alignment": ema_alignment,
        "trend_direction": trend_direction,
        "trend_strength": trend_strength,
        "evidence": {
            "adx_14": adx_latest["adx"],
            "positive_di_14": adx_latest["plus_di"],
            "negative_di_14": adx_latest["minus_di"],
            "di_delta_14": _safe_subtract(adx_latest["plus_di"], adx_latest["minus_di"]),
            "price_above_ema20": _safe_greater(latest_close, ema_20),
            "price_above_ema50": _safe_greater(latest_close, ema_50),
            "price_above_ema100": _safe_greater(latest_close, ema_100),
        },
    }


def _momentum_from_candles(
    candles: list[dict[str, Any]],
    symbol: str,
    interval: str,
) -> dict[str, Any]:
    _require_candles(candles)
    rsi_result = calculate_rsi_from_candles(candles, symbol=symbol, interval=interval, length=14)
    macd_result = calculate_macd_from_candles(candles, symbol=symbol, interval=interval)
    rsi_14 = rsi_result["latest"]
    macd_latest = macd_result["latest"]
    histogram_last_7 = macd_result["values"]["histogram"][-7:]

    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "rsi_14": rsi_14,
        "rsi_state": _rsi_state(rsi_14),
        "rsi_14_last_7": rsi_result["values"][-7:],
        "macd": macd_latest["macd"],
        "macd_signal": macd_latest["signal"],
        "macd_histogram": macd_latest["histogram"],
        "macd_histogram_last_7": histogram_last_7,
        "momentum_bias": _momentum_bias(rsi_14, macd_latest["macd"], macd_latest["signal"], macd_latest["histogram"]),
        "momentum_change": _series_change(histogram_last_7),
    }


def _volatility_from_candles(
    candles: list[dict[str, Any]],
    symbol: str,
    interval: str,
) -> dict[str, Any]:
    _require_candles(candles)
    latest_close = float(candles[-1]["close"])
    atr_14 = calculate_atr_from_candles(candles, symbol=symbol, interval=interval, length=14)["latest"]
    bb_result = calculate_bollinger_bands_from_candles(candles, symbol=symbol, interval=interval)
    bb_latest = bb_result["latest"]
    atr_percent = _percent(atr_14, latest_close)
    bollinger_width_percent = _percent(_safe_subtract(bb_latest["upper"], bb_latest["lower"]), bb_latest["basis"])

    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "latest_close": latest_close,
        "atr_14": atr_14,
        "atr_percent": atr_percent,
        "bollinger_basis": bb_latest["basis"],
        "bollinger_upper": bb_latest["upper"],
        "bollinger_lower": bb_latest["lower"],
        "bollinger_width_percent": bollinger_width_percent,
        "volatility_state": _volatility_state(atr_percent, bollinger_width_percent),
    }


def _support_resistance_from_candles(
    candles: list[dict[str, Any]],
    symbol: str,
    interval: str,
    swing_window: int = 2,
    max_levels: int = 5,
) -> dict[str, Any]:
    _require_candles(candles)
    latest_close = float(candles[-1]["close"])
    recent = candles[-120:]

    support_candidates = []
    resistance_candidates = []

    for i in range(swing_window, len(recent) - swing_window):
        candle = recent[i]
        neighbors = recent[i - swing_window : i] + recent[i + 1 : i + swing_window + 1]
        low = float(candle["low"])
        high = float(candle["high"])

        if all(low <= float(neighbor["low"]) for neighbor in neighbors):
            support_candidates.append(low)
        if all(high >= float(neighbor["high"]) for neighbor in neighbors):
            resistance_candidates.append(high)

    if not support_candidates:
        support_candidates.append(min(float(candle["low"]) for candle in recent))
    if not resistance_candidates:
        resistance_candidates.append(max(float(candle["high"]) for candle in recent))

    support_levels = _cluster_levels(support_candidates, latest_close)
    resistance_levels = _cluster_levels(resistance_candidates, latest_close)
    supports_below = sorted([level for level in support_levels if level < latest_close], reverse=True)
    resistances_above = sorted([level for level in resistance_levels if level > latest_close])

    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "latest_close": latest_close,
        "method": "simple_swing_points",
        "nearest_support": supports_below[0] if supports_below else None,
        "nearest_resistance": resistances_above[0] if resistances_above else None,
        "support_levels": supports_below[:max_levels],
        "resistance_levels": resistances_above[:max_levels],
    }


def _require_candles(candles: list[dict[str, Any]]) -> None:
    if not candles:
        raise ValueError("No candles available")


def _percent_change(current: float | None, baseline: float | None) -> float | None:
    if current is None or baseline in (None, 0):
        return None
    return ((current - baseline) / baseline) * 100


def _percent(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline in (None, 0):
        return None
    return (value / baseline) * 100


def _safe_subtract(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def _safe_greater(left: float | None, right: float | None) -> bool | None:
    if left is None or right is None:
        return None
    return left > right


def _ema_alignment(ema_20: float | None, ema_50: float | None, ema_100: float | None) -> str:
    if None in (ema_20, ema_50, ema_100):
        return "mixed"
    if ema_20 > ema_50 > ema_100:
        return "bullish"
    if ema_20 < ema_50 < ema_100:
        return "bearish"
    return "mixed"


def _trend_direction(
    latest_close: float,
    ema_20: float | None,
    ema_50: float | None,
    ema_100: float | None,
    ema_alignment: str,
    plus_di: float | None,
    minus_di: float | None,
) -> str:
    if None in (ema_20, ema_50, ema_100, plus_di, minus_di):
        return "neutral"

    price_above_all = latest_close > ema_20 and latest_close > ema_50 and latest_close > ema_100
    price_below_all = latest_close < ema_20 and latest_close < ema_50 and latest_close < ema_100

    if ema_alignment == "bullish" and price_above_all and plus_di > minus_di:
        return "bullish"
    if ema_alignment == "bearish" and price_below_all and minus_di > plus_di:
        return "bearish"
    return "neutral"


def _trend_strength(adx: float | None) -> str:
    if adx is None or adx < 20:
        return "weak"
    if adx < 35:
        return "moderate"
    return "strong"


def _rsi_state(rsi: float | None) -> str:
    if rsi is None:
        return "neutral"
    if rsi <= 30:
        return "oversold"
    if rsi >= 70:
        return "overbought"
    return "neutral"


def _momentum_bias(
    rsi: float | None,
    macd: float | None,
    macd_signal: float | None,
    macd_histogram: float | None,
) -> str:
    if None in (rsi, macd, macd_signal, macd_histogram):
        return "neutral"
    if macd > macd_signal and macd_histogram > 0 and rsi >= 50:
        return "bullish"
    if macd < macd_signal and macd_histogram < 0 and rsi <= 50:
        return "bearish"
    return "neutral"


def _series_change(values: list[float | None]) -> str:
    clean = [value for value in values if value is not None]
    if len(clean) < 3:
        return "mixed"

    last_three = clean[-3:]
    if last_three[0] < last_three[1] < last_three[2]:
        return "increasing"
    if last_three[0] > last_three[1] > last_three[2]:
        return "decreasing"
    return "mixed"


def _volatility_state(atr_percent: float | None, bollinger_width_percent: float | None) -> str:
    if atr_percent is None or bollinger_width_percent is None:
        return "normal"
    if atr_percent >= 5 or bollinger_width_percent >= 15:
        return "high"
    if atr_percent <= 1.5 and bollinger_width_percent <= 5:
        return "low"
    return "normal"


def _cluster_levels(levels: list[float], reference_price: float, tolerance_percent: float = 0.35) -> list[float]:
    if not levels:
        return []

    tolerance = reference_price * (tolerance_percent / 100)
    clusters: list[list[float]] = []

    for level in sorted(levels):
        if not clusters or abs(level - clusters[-1][-1]) > tolerance:
            clusters.append([level])
        else:
            clusters[-1].append(level)

    return [sum(cluster) / len(cluster) for cluster in clusters]


def _overall_summary(
    reports: dict[str, dict[str, Any]],
    sentiment: dict[str, Any] | None,
) -> dict[str, Any]:
    trend_votes = [report["trend"]["trend_direction"] for report in reports.values()]
    momentum_votes = [report["momentum"]["momentum_bias"] for report in reports.values()]
    volatility_votes = [report["volatility"]["volatility_state"] for report in reports.values()]

    bullish_score = trend_votes.count("bullish") + momentum_votes.count("bullish")
    bearish_score = trend_votes.count("bearish") + momentum_votes.count("bearish")

    if bullish_score > bearish_score and bullish_score >= 2:
        dominant_bias = "bullish"
    elif bearish_score > bullish_score and bearish_score >= 2:
        dominant_bias = "bearish"
    elif bullish_score == bearish_score and bullish_score > 0:
        dominant_bias = "mixed"
    else:
        dominant_bias = "neutral"

    risk_state = _risk_state(volatility_votes, sentiment)
    notes = _summary_notes(reports, sentiment, dominant_bias, risk_state)

    return {
        "dominant_bias": dominant_bias,
        "risk_state": risk_state,
        "notes": notes,
    }


def _risk_state(volatility_votes: list[str], sentiment: dict[str, Any] | None) -> str:
    high_vol_count = volatility_votes.count("high")
    low_vol_count = volatility_votes.count("low")
    fear_greed_value = sentiment["fear_greed_value"] if sentiment else None
    extreme_sentiment = fear_greed_value is not None and (fear_greed_value <= 20 or fear_greed_value >= 80)

    if high_vol_count >= 2 or (high_vol_count >= 1 and extreme_sentiment):
        return "high"
    if high_vol_count >= 1 or extreme_sentiment:
        return "elevated"
    if low_vol_count == len(volatility_votes) and volatility_votes:
        return "low"
    return "normal"


def _summary_notes(
    reports: dict[str, dict[str, Any]],
    sentiment: dict[str, Any] | None,
    dominant_bias: str,
    risk_state: str,
) -> list[str]:
    notes = [
        f"Dominant technical bias is {dominant_bias}.",
        f"Risk state is {risk_state}.",
    ]

    for interval, report in reports.items():
        trend = report["trend"]
        momentum = report["momentum"]
        volatility = report["volatility"]
        notes.append(
            f"{interval}: trend {trend['trend_direction']} / {trend['trend_strength']}, "
            f"momentum {momentum['momentum_bias']} / {momentum['momentum_change']}, "
            f"volatility {volatility['volatility_state']}."
        )

    if sentiment:
        notes.append(
            f"Fear & Greed is {sentiment['fear_greed_value']} ({sentiment['fear_greed_class']}), "
            f"change {sentiment['change']} from previous."
        )

    return notes
