import numpy as np
import pandas as pd
from app.analytics.mann_kendall import mann_kendall
from app.analytics.sen_slope import sen_slope
from app.analytics.trend import comprehensive_trend_analysis
from app.insights.explanation import explain

def test_mann_kendall_known_directions_and_ties():
    assert mann_kendall([1,2,3,4,5,6,7,8])["trend"] == "increasing"
    assert mann_kendall([8,7,6,5,4,3,2,1])["trend"] == "decreasing"
    flat=mann_kendall([3,3,3,3,3,3])
    assert flat["trend"] == "no_trend" and flat["p_value"] == 1

def test_sen_slope_uses_elapsed_calendar_years():
    times=pd.date_range("2000-01-01",periods=21,freq="YS")
    values=5+2*np.arange(21)
    assert abs(sen_slope(times,values)["slope"]-2)<1e-4

def test_combined_analysis_handles_missing_and_insufficient_data():
    times=pd.date_range("2001-01-01",periods=36,freq="MS")
    values=np.linspace(0,10,36); values[[2,9,18]]=np.nan
    result=comprehensive_trend_analysis(times,values)
    assert result["status"]=="completed"
    assert result["descriptive_stats"]["n_obs"]==33
    assert result["descriptive_stats"]["missing_pct"]>0
    assert result["sens_slope"]["slope"]>0
    assert result["autocorrelation"]["lag1_residual"] is not None
    assert comprehensive_trend_analysis(times[:5],values[:5])["status"]=="insufficient_data"

def test_seasonal_mann_kendall_returns_real_p_value():
    times=pd.date_range("2000-01-01",periods=120,freq="MS")
    values=np.array([float(t.year-2000)+np.sin(t.month*2*np.pi/12) for t in times])
    result=comprehensive_trend_analysis(times,values)
    assert result["seasonal_mann_kendall"]["p_value"] is not None
    assert result["seasonal_mann_kendall"]["seasons_used"]>0

def test_insight_does_not_present_nonsignificant_direction_as_a_finding():
    stats={"status":"completed","mann_kendall":{"trend":"increasing","p_value":.72,"significant":False},
           "sens_slope":{"slope":.001,"ci_lower":-.002,"ci_upper":.003},
           "descriptive_stats":{"n_obs":249},"seasonal_mann_kendall":{"trend":"no_trend","p_value":1.0,"significant":False},
           "autocorrelation":{"significant_autocorr":False}}
    sentence=explain("precipitation",stats,"mm/hr")[0]
    assert "did not detect a statistically significant monotonic trend" in sentence
    assert "the evidence is insufficient to call it a trend" in sentence
    assert "seasonal Mann–Kendall test found no significant trend" in sentence
