"""Variable-specific temporal aggregation dispatch."""
import pandas as pd

def aggregate(frame: pd.DataFrame, rule: str, *, variable: str, accumulation: bool = False) -> pd.DataFrame:
    if rule == "monthly": return frame
    if rule == "daily": raise ValueError("The selected GPM dataset is monthly and cannot be disaggregated to daily values")
    frame=frame.copy().dropna(subset=["value"])
    # Rate products are day-weighted; monthly accumulations are summed.
    frame["weight"]=frame.time.dt.days_in_month if variable=="precipitation" and not accumulation else 1.0
    if rule == "annual": frame["period"]=frame.time.dt.to_period("Y").dt.start_time
    elif rule == "seasonal":
        month=frame.time.dt.month
        frame["season"]=month.map({12:"DJF",1:"DJF",2:"DJF",3:"MAM",4:"MAM",5:"MAM",6:"JJA",7:"JJA",8:"JJA",9:"SON",10:"SON",11:"SON"})
        frame["year"]=frame.time.dt.year.where(month!=12,frame.time.dt.year+1)
        frame["period"]=pd.to_datetime(frame["year"].astype(str)+"-"+frame["season"].map({"DJF":"01","MAM":"04","JJA":"07","SON":"10"})+"-01")
    else: raise ValueError(f"Unsupported temporal resolution: {rule}")
    frame["weighted"]=frame.value*frame.weight
    result=frame.groupby("period",as_index=False).agg(weighted=("weighted","sum"),weight=("weight","sum"))
    result["value"]=result.weighted if accumulation else result.weighted/result.weight
    return result.rename(columns={"period":"time"})[["time","value"]]
