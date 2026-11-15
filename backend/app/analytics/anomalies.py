"""Monthly climatology anomalies without inventing missing observations."""
import numpy as np
import pandas as pd

def monthly_anomalies(times, values):
    frame=pd.DataFrame({"time":pd.to_datetime(times),"value":values})
    frame["month"]=frame.time.dt.month
    baseline=frame.groupby("month").value.transform("mean")
    return [float(x) if np.isfinite(x) else None for x in (frame.value-baseline)]
