"""Mann–Kendall tests with tie-corrected variance."""
from __future__ import annotations
import numpy as np
from scipy.stats import norm

def mann_kendall(values) -> dict:
    x=np.asarray(values,dtype=float); x=x[np.isfinite(x)]; n=len(x)
    if n<3: return {"trend":"insufficient_data","s":None,"variance":None,"z":None,"p_value":None,"tau":None,"significant":None}
    s=sum(np.sign(x[j]-x[i]) for i in range(n-1) for j in range(i+1,n))
    _,counts=np.unique(x,return_counts=True)
    variance=(n*(n-1)*(2*n+5)-sum(t*(t-1)*(2*t+5) for t in counts if t>1))/18
    if variance<=0: z=0.0
    elif s>0: z=(s-1)/np.sqrt(variance)
    elif s<0: z=(s+1)/np.sqrt(variance)
    else: z=0.0
    p=float(2*norm.sf(abs(z))); tau=float(s/(n*(n-1)/2))
    direction="increasing" if s>0 else "decreasing" if s<0 else "no_trend"
    return {"trend":direction,"s":int(s),"variance":float(variance),"z":float(z),"p_value":p,"tau":tau,"significant":bool(p<0.05)}
