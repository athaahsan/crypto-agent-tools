# Crypto Agent Tools

Agent-friendly Python CLI for crypto market data, technical indicators, and deterministic research summaries.

This project is designed to be used by humans and AI agents. Every command returns JSON, and failed commands return structured recovery guidance instead of plain argparse noise.

> Educational tooling only. This is not financial advice and does not place trades.

## For AI Agents

This repo does not require a platform-specific skill file to be useful. The portable interface is the `crypto-agent` CLI.

To ask an AI coding agent to use this repo as a local tool or skill, give it a prompt like this:

```text
I found this repo: https://github.com/athaahsan/crypto-agent-tools

Make this repo usable as a local AI-agent skill.

Use the `crypto-agent` CLI as the main interface. Read the README for setup and usage. Do not rewrite the tool logic.

Do not present results as financial advice.
```

If the agent cannot install the CLI command, tell it to use the fallback:

```bash
python main.py tutorial
python main.py report --symbol BTCUSDT --intervals 1d 4h 1h
```

## Features

- Fetch OHLCV candles from Binance public market data.
- Fetch crypto Fear & Greed Index from alternative.me.
- Fetch latest crypto news from Cointelegraph RSS through rss2json.
- Calculate technical indicators:
  - EMA
  - RSI
  - MACD
  - ADX, +DI, -DI
  - ATR
  - Bollinger Bands
- Build higher-level research summaries:
  - market snapshot
  - trend analysis
  - momentum analysis
  - volatility analysis
  - support/resistance
  - sentiment
  - multi-timeframe report
- Agent-friendly tutorial and JSON error payloads.

## Requirements

- Python 3.10+
- Internet access for live market/news/sentiment data

There are currently no third-party Python dependencies. `requirements.txt` is intentionally empty for now.

## Quick Start

Run directly without installing:

```powershell
python main.py report --symbol BTCUSDT --intervals 1d 4h 1h --pretty
```

Install as a local editable CLI:

```powershell
python -m pip install -e .
```

Then use:

```powershell
crypto-agent report --symbol BTCUSDT --intervals 1d 4h 1h --pretty
```

The old direct style still works:

```powershell
python main.py report --pretty
```

## Output Contract

Successful commands return:

```json
{
  "ok": true,
  "data": {}
}
```

Failed commands return:

```json
{
  "ok": false,
  "error": "What went wrong",
  "tutorial": {}
}
```

This lets an agent recover by reading the response and trying a corrected command.

## Built-In Tutorial

```powershell
crypto-agent tutorial --pretty
```

or:

```powershell
python main.py tutorial --pretty
```

The tutorial returns command examples, common parameters, and all available commands as JSON.

## Common Parameters

Most market and indicator commands support:

| Parameter | Default | Meaning |
|---|---:|---|
| `--symbol` | `BTCUSDT` | Trading pair, such as `ETHUSDT`, `SOLUSDT`, `BNBUSDT`. |
| `--interval` | `1d` | Candle timeframe, such as `1h`, `4h`, `1d`. |
| `--limit` | `300` | Number of candles to fetch. |
| `--timeout` | `20` | HTTP timeout in seconds. |
| `--pretty` | off | Pretty-print JSON for humans. Omit for compact agent output. |

## Market Data Commands

### OHLCV

Fetch raw candles:

```powershell
crypto-agent ohlcv --symbol BTCUSDT --interval 1d --limit 10 --pretty
```

Returns a list of candles with:

- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `close_time`

### Fear & Greed

Fetch Fear & Greed Index:

```powershell
crypto-agent fear-greed --latest --pretty
```

Fetch multiple values:

```powershell
crypto-agent fear-greed --limit 30 --pretty
```

### News

Fetch crypto news:

```powershell
crypto-agent news --limit 5 --pretty
```

Use another RSS feed:

```powershell
crypto-agent news --rss-url https://cointelegraph.com/rss --limit 5 --pretty
```

## Indicator Commands

Indicators fetch OHLCV independently and calculate the requested indicator.

### Output Modes

Return only the latest value:

```powershell
crypto-agent rsi --symbol BTCUSDT --interval 1d --latest-only
```

Return the last N values:

```powershell
crypto-agent rsi --symbol BTCUSDT --interval 1d --last 7
```

Return the full series:

```powershell
crypto-agent rsi --symbol BTCUSDT --interval 1d
```

### EMA

```powershell
crypto-agent ema --symbol BTCUSDT --interval 1d --length 20 --latest-only
```

Options:

- `--length`, default `20`
- `--source`, default `close`; choices: `open`, `high`, `low`, `close`, `volume`

### RSI

```powershell
crypto-agent rsi --symbol BTCUSDT --interval 1d --length 14 --last 7
```

Options:

- `--length`, default `14`
- `--source`, default `close`

### MACD

```powershell
crypto-agent macd --symbol BTCUSDT --interval 1d --last 7
```

Options:

- `--fast-length`, default `12`
- `--slow-length`, default `26`
- `--signal-length`, default `9`
- `--source`, default `close`

For `--last`, MACD returns:

```json
{
  "macd": [],
  "signal": [],
  "histogram": []
}
```

### ADX

```powershell
crypto-agent adx --symbol BTCUSDT --interval 1d --latest-only
```

Options:

- `--di-length`, default `14`
- `--adx-smoothing`, default `14`

Returns ADX, +DI, and -DI.

### ATR

```powershell
crypto-agent atr --symbol BTCUSDT --interval 1d --length 14 --latest-only
```

Options:

- `--length`, default `14`

### Bollinger Bands

```powershell
crypto-agent bb --symbol BTCUSDT --interval 1d --latest-only
```

Alias:

```powershell
crypto-agent bollinger-bands --symbol BTCUSDT --interval 1d --latest-only
```

Options:

- `--length`, default `20`
- `--multiplier`, default `2.0`
- `--source`, default `close`

Returns:

- `basis`
- `upper`
- `lower`

## Research Commands

Research commands combine market data and indicators into compact summaries.

### Snapshot

```powershell
crypto-agent snapshot --symbol BTCUSDT --interval 1d --pretty
```

Returns:

- latest OHLCV values
- candles analyzed
- price change over fetched window
- last 14 closes

### Trend

```powershell
crypto-agent trend --symbol BTCUSDT --interval 1d --pretty
```

Uses EMA 20, EMA 50, EMA 100, and ADX.

Returns:

- `ema_alignment`: `bullish`, `bearish`, or `mixed`
- `trend_direction`: `bullish`, `bearish`, or `neutral`
- `trend_strength`: `weak`, `moderate`, or `strong`
- supporting evidence

### Momentum

```powershell
crypto-agent momentum --symbol BTCUSDT --interval 1d --pretty
```

Uses RSI 14 and MACD 12/26/9.

Returns:

- RSI state
- RSI last 7 values
- MACD values
- MACD histogram last 7 values
- momentum bias
- momentum change

### Volatility

```powershell
crypto-agent volatility --symbol BTCUSDT --interval 1d --pretty
```

Uses ATR 14 and Bollinger Bands.

Returns:

- ATR
- ATR percent
- Bollinger basis/upper/lower
- Bollinger width percent
- volatility state

### Support And Resistance

```powershell
crypto-agent support-resistance --symbol BTCUSDT --interval 1d --pretty
```

Alias:

```powershell
crypto-agent sr --symbol BTCUSDT --interval 1d --pretty
```

This uses a simple swing high/swing low method. It is intentionally basic for v1.

Returns:

- nearest support
- nearest resistance
- support levels
- resistance levels
- method name

### Sentiment

```powershell
crypto-agent sentiment --pretty
```

Returns:

- latest Fear & Greed value
- classification
- previous value
- change
- last 7 values

## Multi-Timeframe Report

The report command is the main agent-facing command.

```powershell
crypto-agent report --symbol BTCUSDT --intervals 1d 4h 1h --pretty
```

Comma-separated intervals also work:

```powershell
crypto-agent report --symbol BTCUSDT --intervals 1d,4h,1h --pretty
```

If intervals are omitted, the default is:

```text
1d 4h 1h
```

The report includes:

- per-interval snapshot
- trend
- momentum
- volatility
- support/resistance
- sentiment
- latest news
- deterministic overall summary

### Report Options

| Option | Default | Meaning |
|---|---:|---|
| `--intervals` | `1d 4h 1h` | Timeframes to analyze. Accepts spaces or commas. |
| `--news-limit` | `5` | Number of news articles to include. |
| `--no-news` | off | Exclude news from the report. |
| `--no-sentiment` | off | Exclude Fear & Greed sentiment. |

Examples:

```powershell
crypto-agent report --symbol ETHUSDT --intervals 1d 4h --news-limit 3 --pretty
```

```powershell
crypto-agent report --symbol BTCUSDT --intervals 1d,4h --no-news --no-sentiment
```

### Overall Summary

`overall_summary` is deterministic and rule-based:

```json
{
  "dominant_bias": "neutral",
  "risk_state": "normal",
  "notes": [
    "Dominant technical bias is neutral.",
    "Risk state is normal."
  ]
}
```

It does not use an LLM. It votes from trend and momentum across intervals, then checks volatility and extreme sentiment.

## Agent Usage Pattern

Recommended first call:

```powershell
crypto-agent tutorial
```

Recommended research call:

```powershell
crypto-agent report --symbol BTCUSDT --intervals 1d 4h 1h
```

Recommended targeted calls:

```powershell
crypto-agent trend --symbol BTCUSDT --interval 1d
crypto-agent momentum --symbol BTCUSDT --interval 4h
crypto-agent rsi --symbol BTCUSDT --interval 1d --last 7
crypto-agent sentiment
```

If the agent gets a command wrong, the CLI returns JSON with:

- the error
- command suggestions
- the tutorial payload

## Project Files

```text
market_data.py   # fetch OHLCV, Fear & Greed, news
indicators.py    # calculate technical indicators
research.py      # high-level deterministic analysis
main.py          # CLI entry point
pyproject.toml   # installable crypto-agent command
```

## Notes And Limitations

- Support/resistance is a simple swing-point approximation, not advanced chart pattern analysis.
- Research summaries are deterministic and do not call an LLM.
- News comes from Cointelegraph RSS through rss2json by default.
- Binance public data is used for OHLCV.
- Network/API failures are returned as JSON errors.

## Development Checks

Compile the Python files:

```powershell
python -m py_compile main.py market_data.py indicators.py research.py
```

Run the tutorial:

```powershell
python main.py tutorial --pretty
```
