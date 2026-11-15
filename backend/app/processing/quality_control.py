"""Non-destructive scientific data checks."""
import numpy as np

def summarize_quality(values) -> dict:
    values=np.asarray(values,dtype=float)
    valid=np.isfinite(values)
    if valid.sum()==0: raise ValueError("No valid observations remain after spatial extraction")
    return {"observation_count":int(valid.sum()),"expected_count":int(values.size),"missing_percentage":float(100*(1-valid.mean())),"minimum":float(np.nanmin(values)),"maximum":float(np.nanmax(values))}
