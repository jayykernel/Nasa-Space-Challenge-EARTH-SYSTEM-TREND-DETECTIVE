"""Combined descriptive, monotonic, seasonal and regression analysis."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import norm
from app.analytics.mann_kendall import mann_kendall
from app.analytics.sen_slope import sen_slope
from app.analytics.regression import linear_regression
from app.analytics.anomalies import monthly_anomalies

def _seasonal_mk(times, values, period=12, alpha=.05):
    t=pd.to_datetime(times); y=np.asarray(values,float); chunks=[]
    for season in range(period):
        sub=y[t.month.to_numpy()%period==season%period]
        sub=sub[np.isfinite(sub)]
        if len(sub)>=3: chunks.append(mann_kendall(sub))
    if not chunks: return {"trend":"insufficient_data","p_value":None,"significant":None,"seasons_used":0}
    s=sum(item["s"] for item in chunks); variance=sum(item["variance"] for item in chunks)
    z=0.0 if variance==0 or s==0 else (s-np.sign(s))/np.sqrt(variance)
    p=float(2*norm.sf(abs(z)))
    return {"trend":"increasing" if s>0 else "decreasing" if s<0 else "no_trend","s":int(s),"z":float(z),"p_value":p,"significant":bool(p<alpha),"seasons_used":len(chunks)}

def comprehensive_trend_analysis(times, values, *, alpha=.05, period=12):
    frame=pd.DataFrame({"time":pd.to_datetime(times,utc=True),"value":values}).sort_values("time").drop_duplicates("time")
    all_values=frame.value.to_numpy(dtype=float); mask=np.isfinite(all_values); valid=all_values[mask]; valid_times=frame.time.to_numpy()[mask]
    n=len(valid); missing=float(100*(1-n/max(len(all_values),1)))
    desc={"n_obs":n,"expected_obs":len(all_values),"missing_pct":missing,"mean":float(np.mean(valid)) if n else None,"std":float(np.std(valid,ddof=1)) if n>1 else None,"min":float(np.min(valid)) if n else None,"max":float(np.max(valid)) if n else None}
    if n<8:
        return {"status":"insufficient_data","linear_regression":linear_regression(valid_times,valid),"mann_kendall":mann_kendall(valid),"seasonal_mann_kendall":{"trend":"insufficient_data","p_value":None,"significant":None,"seasons_used":0},"sens_slope":sen_slope(valid_times,valid),"descriptive_stats":desc,"autocorrelation":{"lag1_residual":None,"significant_autocorr":None,"variance_inflation_factor":None},"anomalies":[]}
    mk=mann_kendall(valid); seasonal=_seasonal_mk(valid_times,valid,period,alpha)
    slope=sen_slope(valid_times,valid,alpha); lr=linear_regression(valid_times,valid)
    timestamps=pd.to_datetime(valid_times,utc=True)
    elapsed=(timestamps.asi8-timestamps.asi8[0])/(365.2425*86400*1e9)
    residuals=valid-np.polyval(np.polyfit(elapsed,valid,1),elapsed)
    lag=float(np.corrcoef(residuals[:-1],residuals[1:])[0,1]) if np.std(residuals[:-1])>0 and np.std(residuals[1:])>0 else 0.0
    significant_ac=bool(abs(lag)>1.96/np.sqrt(n))
    # Approximate AR(1) variance inflation on detrended residuals. Preserve raw p.
    mk["p_value_unadjusted"]=mk["p_value"]
    factor=max(0.1,(1+lag)/(1-lag)) if significant_ac and lag<.95 else (20.0 if significant_ac else 1.0)
    if mk["variance"] and mk["s"] is not None:
        adjusted_variance=mk["variance"]*factor
        z=0.0 if mk["s"]==0 else (mk["s"]-np.sign(mk["s"]))/np.sqrt(adjusted_variance)
        mk["p_value"]=float(2*norm.sf(abs(z))); mk["z"]=float(z); mk["variance_ar1_adjusted"]=float(adjusted_variance)
        mk["significant"]=bool(mk["p_value"]<alpha)
    mk["autocorrelation_adjustment"]="approximate detrended AR(1) variance correction" if significant_ac else "none; residual lag-1 autocorrelation not flagged"
    direction=mk["trend"] if mk["p_value"] is not None and mk["p_value"]<alpha else "no_significant_trend"
    return {"status":"completed","linear_regression":lr,"mann_kendall":mk,"seasonal_mann_kendall":seasonal,"sens_slope":slope,"trend_direction":direction,"is_significant":bool(mk["p_value"]<alpha),"descriptive_stats":desc,"autocorrelation":{"lag1_residual":lag,"significant_autocorr":significant_ac,"variance_inflation_factor":float(factor)},"anomalies":monthly_anomalies(valid_times,valid)}
