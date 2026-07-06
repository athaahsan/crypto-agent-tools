from __future__ import annotations

import argparse
import json
import sys
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from indicators import (
    calculate_adx,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
)
from market_data import fetch_crypto_news, fetch_fear_greed_index, fetch_ohlcv
from research import (
    analyze_momentum,
    analyze_trend,
    analyze_volatility,
    build_market_report,
    find_support_resistance,
    get_crypto_sentiment,
    get_market_snapshot,
)


COMMAND_NAMES = [
    "tutorial",
    "ohlcv",
    "fear-greed",
    "news",
    "ema",
    "rsi",
    "macd",
    "adx",
    "atr",
    "bb",
    "bollinger-bands",
    "snapshot",
    "trend",
    "momentum",
    "volatility",
    "support-resistance",
    "sr",
    "sentiment",
    "report",
]


class AgentArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        payload = {
            "ok": False,
            "error": message,
            "suggestions": _command_suggestions(sys.argv[1:]),
            "tutorial": cli_tutorial(),
        }
        write_json(payload, pretty=True, file=sys.stderr)
        raise SystemExit(2)


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        write_json(
            {
                "ok": False,
                "error": "No command provided.",
                "tutorial": cli_tutorial(),
            },
            pretty=True,
            file=sys.stderr,
        )
        return 2

    args = parser.parse_args()

    try:
        data = run_command(args)
        write_json({"ok": True, "data": data}, pretty=args.pretty)
        return 0
    except Exception as exc:
        write_json({"ok": False, "error": str(exc)}, pretty=True, file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = AgentArgumentParser(
        description="Crypto market data CLI for AI agents.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, parser_class=AgentArgumentParser)

    tutorial = subparsers.add_parser("tutorial", help="Show agent-friendly command examples.")
    add_common_output_args(tutorial)

    ohlcv = subparsers.add_parser("ohlcv", help="Fetch OHLCV candles.")
    add_common_output_args(ohlcv)
    add_market_args(ohlcv)

    fear_greed = subparsers.add_parser("fear-greed", help="Fetch Fear & Greed Index.")
    add_common_output_args(fear_greed)
    fear_greed.add_argument("--limit", type=int, default=30, help="Number of index values.")
    fear_greed.add_argument(
        "--date-format",
        choices=["us", "world", "cn", "kr"],
        help="Optional alternative.me date format. Omit for Unix timestamps.",
    )
    fear_greed.add_argument("--latest", action="store_true", help="Return only the latest value.")
    fear_greed.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds.")

    news = subparsers.add_parser("news", help="Fetch crypto news.")
    add_common_output_args(news)
    news.add_argument("--limit", type=int, default=10, help="Number of articles.")
    news.add_argument(
        "--rss-url",
        default="https://cointelegraph.com/rss",
        help="RSS feed URL to fetch through rss2json.",
    )
    news.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds.")

    ema = subparsers.add_parser("ema", help="Calculate Exponential Moving Average.")
    add_common_output_args(ema)
    add_market_args(ema)
    add_source_arg(ema)
    add_indicator_output_args(ema)
    ema.add_argument("--length", type=int, default=20, help="EMA length.")

    rsi = subparsers.add_parser("rsi", help="Calculate Relative Strength Index.")
    add_common_output_args(rsi)
    add_market_args(rsi)
    add_source_arg(rsi)
    add_indicator_output_args(rsi)
    rsi.add_argument("--length", type=int, default=14, help="RSI length.")

    macd = subparsers.add_parser("macd", help="Calculate MACD.")
    add_common_output_args(macd)
    add_market_args(macd)
    add_source_arg(macd)
    add_indicator_output_args(macd)
    macd.add_argument("--fast-length", type=int, default=12, help="Fast EMA length.")
    macd.add_argument("--slow-length", type=int, default=26, help="Slow EMA length.")
    macd.add_argument("--signal-length", type=int, default=9, help="Signal EMA length.")

    adx = subparsers.add_parser("adx", help="Calculate ADX, +DI, and -DI.")
    add_common_output_args(adx)
    add_market_args(adx)
    add_indicator_output_args(adx)
    adx.add_argument("--di-length", type=int, default=14, help="Directional index length.")
    adx.add_argument("--adx-smoothing", type=int, default=14, help="ADX smoothing length.")

    atr = subparsers.add_parser("atr", help="Calculate Average True Range.")
    add_common_output_args(atr)
    add_market_args(atr)
    add_indicator_output_args(atr)
    atr.add_argument("--length", type=int, default=14, help="ATR length.")

    bollinger_bands = subparsers.add_parser(
        "bb",
        aliases=["bollinger-bands"],
        help="Calculate Bollinger Bands.",
    )
    add_common_output_args(bollinger_bands)
    add_market_args(bollinger_bands)
    add_source_arg(bollinger_bands)
    add_indicator_output_args(bollinger_bands)
    bollinger_bands.add_argument("--length", type=int, default=20, help="Basis SMA length.")
    bollinger_bands.add_argument("--multiplier", type=float, default=2.0, help="Standard deviation multiplier.")

    snapshot = subparsers.add_parser("snapshot", help="Build a compact market snapshot.")
    add_common_output_args(snapshot)
    add_market_args(snapshot)

    trend = subparsers.add_parser("trend", help="Analyze trend using EMA and ADX.")
    add_common_output_args(trend)
    add_market_args(trend)

    momentum = subparsers.add_parser("momentum", help="Analyze momentum using RSI and MACD.")
    add_common_output_args(momentum)
    add_market_args(momentum)

    volatility = subparsers.add_parser("volatility", help="Analyze volatility using ATR and Bollinger Bands.")
    add_common_output_args(volatility)
    add_market_args(volatility)

    support_resistance = subparsers.add_parser(
        "support-resistance",
        aliases=["sr"],
        help="Find simple support and resistance levels.",
    )
    add_common_output_args(support_resistance)
    add_market_args(support_resistance)

    sentiment = subparsers.add_parser("sentiment", help="Summarize crypto Fear & Greed sentiment.")
    add_common_output_args(sentiment)
    sentiment.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds.")

    report = subparsers.add_parser("report", help="Build a multi-timeframe market report.")
    add_common_output_args(report)
    report.add_argument("--symbol", default="BTCUSDT", help="Trading pair, e.g. BTCUSDT.")
    report.add_argument(
        "--intervals",
        nargs="+",
        default=None,
        help="Intervals to analyze. Defaults to: 1d 4h 1h.",
    )
    report.add_argument("--limit", type=int, default=300, help="Number of candles per interval.")
    report.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds.")
    report.add_argument("--news-limit", type=int, default=5, help="Number of news articles to include.")
    report.add_argument("--no-news", action="store_true", help="Exclude news articles from the report.")
    report.add_argument("--no-sentiment", action="store_true", help="Exclude Fear & Greed sentiment from the report.")

    return parser


def add_common_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")


def add_market_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair, e.g. BTCUSDT.")
    parser.add_argument("--interval", default="1d", help="Candle interval, e.g. 1h, 4h, 1d.")
    parser.add_argument("--limit", type=int, default=300, help="Number of candles.")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds.")


def add_source_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--source",
        default="close",
        choices=["open", "high", "low", "close", "volume"],
        help="Candle field used as the indicator source.",
    )


def add_indicator_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--latest-only",
        action="store_true",
        help="Return metadata and the latest value only, without the full series.",
    )
    parser.add_argument(
        "--last",
        type=int,
        help="Return metadata, latest value, and only the last N series values.",
    )


def run_command(args: argparse.Namespace) -> Any:
    if args.command == "tutorial":
        return cli_tutorial()

    if args.command == "ohlcv":
        return fetch_ohlcv(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            timeout=args.timeout,
        )

    if args.command == "fear-greed":
        values = fetch_fear_greed_index(
            limit=args.limit,
            date_format=args.date_format,
            timeout=args.timeout,
        )
        return values[-1] if args.latest and values else values

    if args.command == "news":
        return fetch_crypto_news(
            limit=args.limit,
            rss_url=args.rss_url,
            timeout=args.timeout,
        )

    if args.command == "ema":
        result = calculate_ema(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            length=args.length,
            source=args.source,
            timeout=args.timeout,
        )
        return format_indicator_result(result, args)

    if args.command == "rsi":
        result = calculate_rsi(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            length=args.length,
            source=args.source,
            timeout=args.timeout,
        )
        return format_indicator_result(result, args)

    if args.command == "macd":
        result = calculate_macd(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            fast_length=args.fast_length,
            slow_length=args.slow_length,
            signal_length=args.signal_length,
            source=args.source,
            timeout=args.timeout,
        )
        return format_indicator_result(result, args)

    if args.command == "adx":
        result = calculate_adx(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            di_length=args.di_length,
            adx_smoothing=args.adx_smoothing,
            timeout=args.timeout,
        )
        return format_indicator_result(result, args)

    if args.command == "atr":
        result = calculate_atr(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            length=args.length,
            timeout=args.timeout,
        )
        return format_indicator_result(result, args)

    if args.command in {"bb", "bollinger-bands"}:
        result = calculate_bollinger_bands(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            length=args.length,
            multiplier=args.multiplier,
            source=args.source,
            timeout=args.timeout,
        )
        return format_indicator_result(result, args)

    if args.command == "snapshot":
        return get_market_snapshot(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            timeout=args.timeout,
        )

    if args.command == "trend":
        return analyze_trend(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            timeout=args.timeout,
        )

    if args.command == "momentum":
        return analyze_momentum(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            timeout=args.timeout,
        )

    if args.command == "volatility":
        return analyze_volatility(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            timeout=args.timeout,
        )

    if args.command in {"support-resistance", "sr"}:
        return find_support_resistance(
            symbol=args.symbol,
            interval=args.interval,
            limit=args.limit,
            timeout=args.timeout,
        )

    if args.command == "sentiment":
        return get_crypto_sentiment(timeout=args.timeout)

    if args.command == "report":
        return build_market_report(
            symbol=args.symbol,
            intervals=args.intervals,
            limit=args.limit,
            timeout=args.timeout,
            include_sentiment=not args.no_sentiment,
            include_news=not args.no_news,
            news_limit=args.news_limit,
        )

    raise ValueError(f"Unknown command: {args.command}")


def format_indicator_result(result: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if args.last is not None:
        if args.last < 1:
            raise ValueError("--last must be greater than 0")

        compact = compact_indicator_result(result)
        compact["last"] = last_indicator_values(result["values"], args.last)
        return compact

    if args.latest_only:
        return compact_indicator_result(result)

    return result


def compact_indicator_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "indicator": result["indicator"],
        "symbol": result["symbol"],
        "interval": result["interval"],
        "parameters": result["parameters"],
        "latest": result["latest"],
    }


def last_indicator_values(values: Any, count: int) -> Any:
    if isinstance(values, dict):
        return {key: series[-count:] for key, series in values.items()}
    return values[-count:]


def cli_tutorial() -> dict[str, Any]:
    command = _command_prefix()
    return {
        "purpose": "Fetch crypto market data, calculate indicators, and build research summaries as JSON.",
        "output_contract": {
            "success": {"ok": True, "data": "..."},
            "failure": {"ok": False, "error": "...", "tutorial": "..."},
        },
        "install_for_cli_command": {
            "command": "python -m pip install -e .",
            "result": "Enables the crypto-agent command from this project environment.",
        },
        "default_symbol": "BTCUSDT",
        "common_parameters": {
            "--symbol": "Trading pair, e.g. BTCUSDT, ETHUSDT, SOLUSDT.",
            "--interval": "Candle timeframe, e.g. 1h, 4h, 1d.",
            "--limit": "Number of candles to fetch.",
            "--pretty": "Pretty-print JSON for humans. Omit for compact agent output.",
            "--timeout": "HTTP timeout in seconds.",
        },
        "recommended_agent_commands": [
            f"{command} report --symbol BTCUSDT --intervals 1d 4h 1h",
            f"{command} report --symbol BTCUSDT --intervals 1d,4h,1h",
            f"{command} trend --symbol BTCUSDT --interval 1d",
            f"{command} momentum --symbol BTCUSDT --interval 1d",
            f"{command} volatility --symbol BTCUSDT --interval 1d",
            f"{command} support-resistance --symbol BTCUSDT --interval 1d",
            f"{command} sentiment",
        ],
        "indicator_examples": [
            f"{command} rsi --symbol BTCUSDT --interval 1d --length 14 --latest-only",
            f"{command} rsi --symbol BTCUSDT --interval 1d --length 14 --last 7",
            f"{command} macd --symbol BTCUSDT --interval 1d --last 7",
            f"{command} bb --symbol BTCUSDT --interval 1d --latest-only",
        ],
        "available_commands": COMMAND_NAMES,
    }


def _command_suggestions(argv: list[str]) -> list[str]:
    command = _command_prefix()
    if not argv:
        return [f"{command} tutorial"]

    maybe_command = argv[0]
    if maybe_command.startswith("-"):
        return [f"{command} tutorial"]

    matches = get_close_matches(maybe_command, COMMAND_NAMES, n=3, cutoff=0.45)
    if matches:
        return [f"{command} {match} --help" for match in matches]

    return [f"{command} tutorial"]


def _command_prefix() -> str:
    executable = Path(sys.argv[0]).name
    stem = Path(sys.argv[0]).stem
    if stem == "crypto-agent":
        return "crypto-agent"
    if executable == "main.py":
        return "python main.py"
    return executable


def write_json(payload: dict[str, Any], pretty: bool, file: Any = sys.stdout) -> None:
    if pretty:
        json.dump(payload, file, indent=2, ensure_ascii=False)
    else:
        json.dump(payload, file, separators=(",", ":"), ensure_ascii=False)
    file.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
