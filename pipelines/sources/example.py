"""Example pipeline. Copy this as a template for real sources."""

import pandas as pd

from ..base import Pipeline
from ..registry import register


@register
class ExamplePipeline(Pipeline):
    name = "example"

    def fetch(self) -> pd.DataFrame:
        # Real pipelines fetch from a free source here; this returns synthetic rows.
        return pd.DataFrame(
            {
                "TS": ["2026-01-01", "2026-01-02", "2026-01-03"],
                "primary_id": ["AAPL", "AAPL", "AAPL"],
                "value": [100.0, 101.5, 99.8],
            }
        )
