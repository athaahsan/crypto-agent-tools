from __future__ import annotations

import math
from typing import Any

from market_data import fetch_ohlcv


Series = list[float | None]


def calculate_ema_from_candles(
    candles: list[dict[str, Any]],
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    length: int = 20,
    source: str = "close",
) -> dict[str, Any]:
    values = _ema_series(_source_values(candles, source), length)
    return _indicator_result("ema", symbol, interval, {"length": length, "source": source}, values)


def calculate_ema(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    length: int = 20,
    source: str = "close",
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return calculate_ema_from_candles(candles, symbol=symbol, interval=interval, length=length, source=source)


def calculate_rsi_from_candles(
    candles: list[dict[str, Any]],
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    length: int = 14,
    source: str = "close",
) -> dict[str, Any]:
    values = _rsi_series(_source_values(candles, source), length)
    return _indicator_result("rsi", symbol, interval, {"length": length, "source": source}, values)


def calculate_rsi(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    length: int = 14,
    source: str = "close",
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return calculate_rsi_from_candles(candles, symbol=symbol, interval=interval, length=length, source=source)


def calculate_macd_from_candles(
    candles: list[dict[str, Any]],
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    fast_length: int = 12,
    slow_length: int = 26,
    signal_length: int = 9,
    source: str = "close",
) -> dict[str, Any]:
    source_values = _source_values(candles, source)
    macd, signal, histogram = _macd_series(
        source_values,
        fast_length=fast_length,
        slow_length=slow_length,
        signal_length=signal_length,
    )
    return {
        "indicator": "macd",
        "symbol": symbol.upper(),
        "interval": interval,
        "parameters": {
            "fast_length": fast_length,
            "slow_length": slow_length,
            "signal_length": signal_length,
            "source": source,
        },
        "latest": {
            "macd": _latest(macd),
            "signal": _latest(signal),
            "histogram": _latest(histogram),
        },
        "values": {
            "macd": macd,
            "signal": signal,
            "histogram": histogram,
        },
    }


def calculate_macd(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    fast_length: int = 12,
    slow_length: int = 26,
    signal_length: int = 9,
    source: str = "close",
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return calculate_macd_from_candles(
        candles,
        symbol=symbol,
        interval=interval,
        fast_length=fast_length,
        slow_length=slow_length,
        signal_length=signal_length,
        source=source,
    )


def calculate_adx_from_candles(
    candles: list[dict[str, Any]],
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    di_length: int = 14,
    adx_smoothing: int = 14,
) -> dict[str, Any]:
    adx, plus_di, minus_di = _adx_series(
        highs=_source_values(candles, "high"),
        lows=_source_values(candles, "low"),
        closes=_source_values(candles, "close"),
        di_length=di_length,
        adx_smoothing=adx_smoothing,
    )
    return {
        "indicator": "adx",
        "symbol": symbol.upper(),
        "interval": interval,
        "parameters": {
            "di_length": di_length,
            "adx_smoothing": adx_smoothing,
        },
        "latest": {
            "adx": _latest(adx),
            "plus_di": _latest(plus_di),
            "minus_di": _latest(minus_di),
        },
        "values": {
            "adx": adx,
            "plus_di": plus_di,
            "minus_di": minus_di,
        },
    }


def calculate_adx(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    di_length: int = 14,
    adx_smoothing: int = 14,
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return calculate_adx_from_candles(
        candles,
        symbol=symbol,
        interval=interval,
        di_length=di_length,
        adx_smoothing=adx_smoothing,
    )


def calculate_atr_from_candles(
    candles: list[dict[str, Any]],
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    length: int = 14,
) -> dict[str, Any]:
    values = _atr_series(
        highs=_source_values(candles, "high"),
        lows=_source_values(candles, "low"),
        closes=_source_values(candles, "close"),
        length=length,
    )
    return _indicator_result("atr", symbol, interval, {"length": length}, values)


def calculate_atr(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    length: int = 14,
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return calculate_atr_from_candles(candles, symbol=symbol, interval=interval, length=length)


def calculate_bollinger_bands_from_candles(
    candles: list[dict[str, Any]],
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    length: int = 20,
    multiplier: float = 2.0,
    source: str = "close",
) -> dict[str, Any]:
    basis, upper, lower = _bollinger_bands_series(
        _source_values(candles, source),
        length=length,
        multiplier=multiplier,
    )
    return {
        "indicator": "bollinger_bands",
        "symbol": symbol.upper(),
        "interval": interval,
        "parameters": {
            "length": length,
            "multiplier": multiplier,
            "source": source,
        },
        "latest": {
            "basis": _latest(basis),
            "upper": _latest(upper),
            "lower": _latest(lower),
        },
        "values": {
            "basis": basis,
            "upper": upper,
            "lower": lower,
        },
    }


def calculate_bollinger_bands(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    limit: int = 300,
    length: int = 20,
    multiplier: float = 2.0,
    source: str = "close",
    timeout: int = 20,
) -> dict[str, Any]:
    candles = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit, timeout=timeout)
    return calculate_bollinger_bands_from_candles(
        candles,
        symbol=symbol,
        interval=interval,
        length=length,
        multiplier=multiplier,
        source=source,
    )


def _indicator_result(
    indicator: str,
    symbol: str,
    interval: str,
    parameters: dict[str, Any],
    values: Series,
) -> dict[str, Any]:
    return {
        "indicator": indicator,
        "symbol": symbol.upper(),
        "interval": interval,
        "parameters": parameters,
        "latest": _latest(values),
        "values": values,
    }


def _source_values(candles: list[dict[str, Any]], source: str) -> list[float]:
    valid_sources = {"open", "high", "low", "close", "volume"}
    if source not in valid_sources:
        raise ValueError(f"Unsupported source '{source}'. Use one of: {sorted(valid_sources)}")
    return [float(candle[source]) for candle in candles]


def _validate_length(length: int, name: str = "length") -> None:
    if length < 1:
        raise ValueError(f"{name} must be greater than 0")


def _latest(values: Series) -> float | None:
    for value in reversed(values):
        if value is not None:
            return value
    return None


def _ema_series(values: list[float], length: int) -> Series:
    _validate_length(length)
    if not values:
        return []

    alpha = 2 / (length + 1)
    ema: Series = [float(values[0])]
    for value in values[1:]:
        previous = ema[-1]
        ema.append(alpha * float(value) + (1 - alpha) * float(previous))
    return ema


def _rsi_series(values: list[float], length: int) -> Series:
    _validate_length(length)
    if len(values) <= length:
        return [None] * len(values)

    rsi: Series = [None] * len(values)
    gains = [0.0] * len(values)
    losses = [0.0] * len(values)

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains[i] = max(change, 0.0)
        losses[i] = max(-change, 0.0)

    avg_gain = sum(gains[1 : length + 1]) / length
    avg_loss = sum(losses[1 : length + 1]) / length
    rsi[length] = _rsi_value(avg_gain, avg_loss)

    alpha = 1 / length
    for i in range(length + 1, len(values)):
        avg_gain = alpha * gains[i] + (1 - alpha) * avg_gain
        avg_loss = alpha * losses[i] + (1 - alpha) * avg_loss
        rsi[i] = _rsi_value(avg_gain, avg_loss)

    return rsi


def _rsi_value(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    if avg_gain == 0:
        return 0.0
    relative_strength = avg_gain / avg_loss
    return 100 - (100 / (1 + relative_strength))


def _macd_series(
    values: list[float],
    fast_length: int,
    slow_length: int,
    signal_length: int,
) -> tuple[Series, Series, Series]:
    _validate_length(fast_length, "fast_length")
    _validate_length(slow_length, "slow_length")
    _validate_length(signal_length, "signal_length")

    fast_ema = _ema_series(values, fast_length)
    slow_ema = _ema_series(values, slow_length)
    macd = [
        None if fast is None or slow is None else float(fast) - float(slow)
        for fast, slow in zip(fast_ema, slow_ema)
    ]
    signal = _ema_series(_none_to_zero(macd), signal_length)
    histogram = [
        None if line is None or sig is None else float(line) - float(sig)
        for line, sig in zip(macd, signal)
    ]
    return macd, signal, histogram


def _atr_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    length: int,
) -> Series:
    true_range = _true_range_series(highs, lows, closes)
    return _rma_series(true_range, length)


def _adx_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    di_length: int,
    adx_smoothing: int,
) -> tuple[Series, Series, Series]:
    _validate_length(di_length, "di_length")
    _validate_length(adx_smoothing, "adx_smoothing")

    n = len(closes)
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n

    for i in range(1, n):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        plus_dm[i] = up_move if up_move > down_move and up_move > 0 else 0.0
        minus_dm[i] = down_move if down_move > up_move and down_move > 0 else 0.0

    true_range = _true_range_series(highs, lows, closes)
    smoothed_tr = _rma_series(true_range, di_length)
    smoothed_plus_dm = _rma_series(plus_dm, di_length)
    smoothed_minus_dm = _rma_series(minus_dm, di_length)

    plus_di: Series = [None] * n
    minus_di: Series = [None] * n
    dx: Series = [None] * n

    for i in range(n):
        tr = smoothed_tr[i]
        plus = smoothed_plus_dm[i]
        minus = smoothed_minus_dm[i]
        if tr is None or plus is None or minus is None or tr == 0:
            continue

        plus_di[i] = 100 * plus / tr
        minus_di[i] = 100 * minus / tr
        di_sum = plus_di[i] + minus_di[i]
        dx[i] = 0.0 if di_sum == 0 else 100 * abs(plus_di[i] - minus_di[i]) / di_sum

    adx = _rma_series(dx, adx_smoothing)
    return adx, plus_di, minus_di


def _bollinger_bands_series(
    values: list[float],
    length: int,
    multiplier: float,
) -> tuple[Series, Series, Series]:
    _validate_length(length)
    if multiplier < 0:
        raise ValueError("multiplier must be greater than or equal to 0")

    basis: Series = [None] * len(values)
    upper: Series = [None] * len(values)
    lower: Series = [None] * len(values)

    for i in range(length - 1, len(values)):
        window = values[i - length + 1 : i + 1]
        average = sum(window) / length
        variance = sum((value - average) ** 2 for value in window) / length
        deviation = multiplier * math.sqrt(variance)
        basis[i] = average
        upper[i] = average + deviation
        lower[i] = average - deviation

    return basis, upper, lower


def _rma_series(values: list[float] | Series, length: int) -> Series:
    _validate_length(length)
    result: Series = [None] * len(values)
    alpha = 1 / length

    valid_seen = 0
    seed_total = 0.0
    previous: float | None = None

    for i, value in enumerate(values):
        if value is None:
            continue

        numeric_value = float(value)
        if previous is None:
            valid_seen += 1
            seed_total += numeric_value
            if valid_seen == length:
                previous = seed_total / length
                result[i] = previous
            continue

        previous = alpha * numeric_value + (1 - alpha) * previous
        result[i] = previous

    return result


def _true_range_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
) -> list[float]:
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("highs, lows, and closes must have the same length")

    true_range = [0.0] * len(closes)
    for i in range(len(closes)):
        high_low = highs[i] - lows[i]
        if i == 0:
            true_range[i] = high_low
            continue

        high_close = abs(highs[i] - closes[i - 1])
        low_close = abs(lows[i] - closes[i - 1])
        true_range[i] = max(high_low, high_close, low_close)

    return true_range


def _none_to_zero(values: Series) -> list[float]:
    return [0.0 if value is None else float(value) for value in values]
