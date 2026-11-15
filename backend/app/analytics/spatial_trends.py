"""Per-cell trend summaries from actual regional grid-cell series."""
from app.analytics.mann_kendall import mann_kendall
from app.analytics.sen_slope import sen_slope

def spatial_trends(cells, times):
    result=[]
    for cell in cells:
        mk=mann_kendall(cell["series"]); slope=sen_slope(times,cell["series"])
        direction="insufficient_data" if mk["trend"]=="insufficient_data" else (mk["trend"] if mk["significant"] is True else "no_significant_trend")
        result.append({"lat":cell["lat"],"lon":cell["lon"],"trend_direction":direction,"trend_magnitude":slope["slope"],"p_value":mk["p_value"],"significance":mk["significant"] is True,"n_obs":sum(x is not None for x in cell["series"])})
    return result
