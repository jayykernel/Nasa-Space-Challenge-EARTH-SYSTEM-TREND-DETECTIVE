"""Time-index cleaning for normalized regional observations."""
import pandas as pd

def clean_series(time_values, data_values):
    frame=pd.DataFrame({"time":pd.to_datetime(time_values,utc=True),"value":data_values})
    frame=frame.drop_duplicates("time",keep="last").sort_values("time").reset_index(drop=True)
    return frame
