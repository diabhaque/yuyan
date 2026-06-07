"""Daily adjusted-close prices for MAGS / SMH / DRAM constituents (via Yahoo)."""

import polars as pl
import yfinance as yf

from ..base import Pipeline
from ..registry import register

# Point-in-time holdings snapshots (Yahoo symbols), sourced 2026-06-07.
MAGS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
SMH = [
    "NVDA", "TSM", "MU", "AMD", "INTC", "AVGO", "QCOM", "MRVL", "TXN", "LRCX",
    "KLAC", "AMAT", "ASML", "ADI", "CDNS", "SNPS", "STM", "NXPI", "ARM", "TER",
    "MPWR", "MCHP", "ALAB", "ON", "SWKS",
]
# DRAM equities only. Skipped non-equity holdings: a US T-bill, 5 swap line items,
# and KRW/TWD currency positions (can't be priced as tickers).
DRAM = ["000660.KS", "005930.KS", "285A.T", "SNDK", "STX", "WDC", "MU", "2408.TW", "2344.TW"]


# yfinance prices each listing in its native currency, keyed by Yahoo suffix.
SUFFIX_CURRENCY = {".KS": "KRW", ".TW": "TWD", ".T": "JPY"}


def currency_of(ticker: str) -> str:
    for suffix, ccy in SUFFIX_CURRENCY.items():
        if ticker.endswith(suffix):
            return ccy
    return "USD"  # US listings, including ADRs (TSM, ASML, ARM, ...)


@register
class PricesPipeline(Pipeline):
    name = "prices"
    tickers = sorted(set(MAGS + SMH + DRAM))

    def fetch(self):
        data = yf.download(self.tickers, period="max", auto_adjust=True, progress=False)
        close = data["Close"]  # date index, one column per ticker (adjusted close)

        currency = {t: currency_of(t) for t in self.tickers}
        long = (
            pl.from_pandas(close.reset_index())  # yfinance is pandas; cross to polars here
            .unpivot(index="Date", variable_name="primary_id", value_name="value")
            .drop_nulls("value")
            .with_columns(
                pl.col("Date").dt.strftime("%Y-%m-%d").alias("TS"),
                pl.col("primary_id").replace(currency).alias("currency"),
            )
            .select("TS", "primary_id", "value", "currency")
        )

        missing = [t for t in self.tickers if t not in close.columns or close[t].isna().all()]
        if missing:
            print(f"prices: no data for {missing}")

        return long
