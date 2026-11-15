"""Tabular provider adapter with strict time/value/unit expectations."""
import pandas as pd

def normalize_dataframe(frame: pd.DataFrame, *, time_column: str, value_column: str, units: str) -> pd.DataFrame:
    if time_column not in frame or value_column not in frame or not units.strip():
        raise ValueError("Table must contain the requested time/value columns and known units")
    result = frame[[time_column, value_column]].rename(columns={time_column:"time", value_column:"value"}).copy()
    result["time"] = pd.to_datetime(result["time"], errors="coerce", utc=True)
    result["value"] = pd.to_numeric(result["value"], errors="coerce")
    result = result.dropna(subset=["time"]).drop_duplicates("time").sort_values("time")
    result.attrs["units"] = units
    return result
