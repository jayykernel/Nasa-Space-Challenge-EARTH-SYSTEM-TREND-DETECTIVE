"""Sen median pairwise slope and confidence interval in value units/year."""
import numpy as np
import pandas as pd
from scipy.stats import theilslopes

def sen_slope(times, values, alpha: float = .05) -> dict:
    t=pd.to_datetime(times,utc=True).tz_localize(None).to_numpy(dtype="datetime64[ns]"); y=np.asarray(values,dtype=float)
    mask=np.isfinite(y)&~np.isnat(t); t,y=t[mask],y[mask]
    if len(y)<3: return {"slope":None,"ci_lower":None,"ci_upper":None,"unit":"per year"}
    years=(t-t[0]).astype("timedelta64[s]").astype(float)/(365.2425*86400)
    fit=theilslopes(y,years,alpha=1-alpha)
    return {"slope":float(fit.slope),"ci_lower":float(fit.low_slope),"ci_upper":float(fit.high_slope),"unit":"per year"}
