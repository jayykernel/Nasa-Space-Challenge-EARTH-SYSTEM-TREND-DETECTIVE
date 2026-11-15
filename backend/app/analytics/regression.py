"""Ordinary least squares with elapsed years as the x coordinate."""
import numpy as np
import pandas as pd
from scipy.stats import linregress

def linear_regression(times, values):
    t=pd.to_datetime(times,utc=True).tz_localize(None).to_numpy(dtype="datetime64[ns]"); y=np.asarray(values,dtype=float)
    mask=np.isfinite(y)&~np.isnat(t); t,y=t[mask],y[mask]
    if len(y)<3: return {"slope":None,"intercept":None,"r_squared":None,"p_value":None,"stderr":None,"n_obs":int(len(y)),"unit":"per year"}
    x=(t-t[0]).astype("timedelta64[s]").astype(float)/(365.2425*86400)
    fit=linregress(x,y)
    return {"slope":float(fit.slope),"intercept":float(fit.intercept),"r_squared":float(fit.rvalue**2),"p_value":float(fit.pvalue),"stderr":float(fit.stderr),"n_obs":int(len(y)),"unit":"per year"}
