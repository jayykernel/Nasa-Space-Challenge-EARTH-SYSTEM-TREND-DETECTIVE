"""Statistical analysis engine for trend detection."""
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import linregress
import pymannkendall as mk
from typing import Any
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)


def linear_regression_analysis(time_values: np.ndarray, data_values: np.ndarray) -> dict[str, float]:
    """
    Perform linear regression on time series data.

    Args:
        time_values: Time values (e.g., year fractions)
        data_values: Data values

    Returns:
        Dict with slope, intercept, r_squared, std_err, p_value
    """
    # Remove NaN values
    mask = ~np.isnan(data_values) & ~np.isnan(time_values)
    if mask.sum() < 3:
        return {
            "slope": np.nan,
            "intercept": np.nan,
            "r_squared": np.nan,
            "std_err": np.nan,
            "p_value": np.nan,
            "n_obs": int(mask.sum()),
        }

    t_clean = time_values[mask]
    d_clean = data_values[mask]

    result = linregress(t_clean, d_clean)

    return {
        "slope": float(result.slope),
        "intercept": float(result.intercept),
        "r_squared": float(result.rvalue**2),
        "std_err": float(result.stderr),
        "p_value": float(result.pvalue),
        "n_obs": int(mask.sum()),
    }


def mann_kendall_test(data_values: np.ndarray, alpha: float = 0.05) -> dict[str, Any]:
    """
    Perform Mann-Kendall trend test.

    Args:
        data_values: Time series data
        alpha: Significance level

    Returns:
        Dict with test statistics
    """
    # Remove NaN values
    clean_data = data_values[~np.isnan(data_values)]

    if len(clean_data) < 4:
        return {
            "trend": "insufficient_data",
            "h": False,
            "p_value": np.nan,
            "z": np.nan,
            "tau": np.nan,
            "s": np.nan,
            "var_s": np.nan,
            "alpha": alpha,
        }

    # Use pymannkendall
    result = mk.original_test(clean_data, alpha=alpha)

    return {
        "trend": result.trend,  # 'increasing', 'decreasing', 'no trend'
        "h": bool(result.h),  # True if trend is significant
        "p_value": float(result.p),
        "z": float(result.z),
        "tau": float(result.Tau),
        "s": float(result.s),
        "var_s": float(result.var_s),
        "alpha": alpha,
        "n_obs": len(clean_data),
    }


def seasonal_mann_kendall_test(data_values: np.ndarray, period: int = 12, alpha: float = 0.05) -> dict[str, Any]:
    """
    Perform Seasonal Mann-Kendall test for data with seasonality.

    Args:
        data_values: Time series data
        period: Number of seasons (12 for monthly data)
        alpha: Significance level

    Returns:
        Dict with test statistics
    """
    clean_data = data_values[~np.isnan(data_values)]

    if len(clean_data) < period * 2:
        return {
            "trend": "insufficient_data",
            "h": False,
            "p_value": np.nan,
            "z": np.nan,
            "tau": np.nan,
            "alpha": alpha,
            "period": period,
        }

    result = mk.seasonal_test(clean_data, period=period, alpha=alpha)

    return {
        "trend": result.trend,
        "h": bool(result.h),
        "p_value": float(result.p),
        "z": float(result.z),
        "tau": float(result.Tau),
        "alpha": alpha,
        "period": period,
        "n_obs": len(clean_data),
    }


def sens_slope(data_values: np.ndarray, time_values: np.ndarray | None = None, alpha: float = 0.05) -> dict[str, Any]:
    """
    Compute Sen's slope (Theil-Sen estimator) for robust trend magnitude.

    Args:
        data_values: Time series data
        time_values: Optional time values (if not provided, uses 0, 1, 2, ...)
        alpha: Confidence level

    Returns:
        Dict with slope, confidence interval, and metadata
    """
    clean_mask = ~np.isnan(data_values)
    d_clean = data_values[clean_mask]

    if len(d_clean) < 3:
        return {
            "slope": np.nan,
            "intercept": np.nan,
            "ci_lower": np.nan,
            "ci_upper": np.nan,
            "alpha": alpha,
            "n_obs": int(clean_mask.sum()),
        }

    if time_values is not None:
        t_clean = time_values[clean_mask]
    else:
        t_clean = np.arange(len(d_clean))

    # Use pymannkendall's sens_slope
    result = mk.sens_slope(d_clean, alpha=alpha)

    return {
        "slope": float(result.slope),
        "intercept": float(result.intercept),
        "ci_lower": float(result.slope - 1.96 * result.slope_std) if hasattr(result, 'slope_std') else np.nan,
        "ci_upper": float(result.slope + 1.96 * result.slope_std) if hasattr(result, 'slope_std') else np.nan,
        "alpha": alpha,
        "n_obs": len(d_clean),
    }


def descriptive_statistics(data_values: np.ndarray) -> dict[str, float]:
    """
    Compute descriptive statistics.

    Args:
        data_values: Time series data

    Returns:
        Dict with descriptive statistics
    """
    clean_data = data_values[~np.isnan(data_values)]

    if len(clean_data) == 0:
        return {
            "mean": np.nan,
            "median": np.nan,
            "std": np.nan,
            "min": np.nan,
            "max": np.nan,
            "range": np.nan,
            "q25": np.nan,
            "q75": np.nan,
            "iqr": np.nan,
            "cv": np.nan,  # coefficient of variation
            "skewness": np.nan,
            "kurtosis": np.nan,
            "n_obs": 0,
            "n_missing": len(data_values),
            "missing_pct": 100.0,
        }

    return {
        "mean": float(np.mean(clean_data)),
        "median": float(np.median(clean_data)),
        "std": float(np.std(clean_data, ddof=1)),
        "min": float(np.min(clean_data)),
        "max": float(np.max(clean_data)),
        "range": float(np.max(clean_data) - np.min(clean_data)),
        "q25": float(np.percentile(clean_data, 25)),
        "q75": float(np.percentile(clean_data, 75)),
        "iqr": float(np.percentile(clean_data, 75) - np.percentile(clean_data, 25)),
        "cv": float(np.std(clean_data, ddof=1) / np.mean(clean_data)) if np.mean(clean_data) != 0 else np.nan,
        "skewness": float(stats.skew(clean_data)),
        "kurtosis": float(stats.kurtosis(clean_data)),
        "n_obs": len(clean_data),
        "n_missing": len(data_values) - len(clean_data),
        "missing_pct": float((len(data_values) - len(clean_data)) / len(data_values) * 100),
    }


def compute_anomalies(data_values: np.ndarray, time_values: np.ndarray | None = None,
                      reference_period: tuple[int, int] | None = None) -> dict[str, Any]:
    """
    Compute anomalies relative to a reference period or overall mean.

    Args:
        data_values: Time series data
        time_values: Optional time values (year fractions)
        reference_period: Optional (start_year, end_year) for reference period

    Returns:
        Dict with anomalies and reference info
    """
    clean_mask = ~np.isnan(data_values)
    d_clean = data_values[clean_mask]

    if len(d_clean) == 0:
        return {
            "anomalies": np.full_like(data_values, np.nan),
            "reference_mean": np.nan,
            "reference_period": reference_period,
        }

    if reference_period is not None and time_values is not None:
        t_clean = time_values[clean_mask]
        ref_mask = (t_clean >= reference_period[0]) & (t_clean <= reference_period[1])
        if ref_mask.sum() > 0:
            ref_mean = np.mean(d_clean[ref_mask])
        else:
            ref_mean = np.mean(d_clean)
    else:
        ref_mean = np.mean(d_clean)

    anomalies = np.full_like(data_values, np.nan)
    anomalies[clean_mask] = d_clean - ref_mean

    return {
        "anomalies": anomalies,
        "reference_mean": float(ref_mean),
        "reference_period": reference_period,
    }


def seasonal_decompose(data_values: np.ndarray, time_values: np.ndarray | None = None,
                       period: int = 12) -> dict[str, Any]:
    """
    Simple seasonal decomposition for monthly data.

    Args:
        data_values: Time series data
        time_values: Optional time values
        period: Number of time steps per cycle (12 for monthly)

    Returns:
        Dict with trend, seasonal, and residual components
    """
    from statsmodels.tsa.seasonal import seasonal_decompose as sm_decompose

    clean_mask = ~np.isnan(data_values)

    if clean_mask.sum() < period * 2:
        return {
            "trend": np.full_like(data_values, np.nan),
            "seasonal": np.full_like(data_values, np.nan),
            "residual": np.full_like(data_values, np.nan),
            "error": "Insufficient data for seasonal decomposition",
        }

    # Create a pandas Series with datetime index for statsmodels
    if time_values is not None:
        # Convert year fractions to datetime
        dates = [pd.Timestamp(year=int(t), month=int((t % 1) * 12) + 1, day=1) for t in time_values[clean_mask]]
    else:
        dates = pd.date_range(start='2000-01-01', periods=clean_mask.sum(), freq='MS')

    series = pd.Series(data_values[clean_mask], index=dates)

    try:
        result = sm_decompose(series, model='additive', period=period)

        trend = np.full_like(data_values, np.nan)
        seasonal = np.full_like(data_values, np.nan)
        residual = np.full_like(data_values, np.nan)

        trend[clean_mask] = result.trend.values
        seasonal[clean_mask] = result.seasonal.values
        residual[clean_mask] = result.resid.values

        return {
            "trend": trend,
            "seasonal": seasonal,
            "residual": residual,
            "period": period,
        }
    except Exception as e:
        return {
            "trend": np.full_like(data_values, np.nan),
            "seasonal": np.full_like(data_values, np.nan),
            "residual": np.full_like(data_values, np.nan),
            "error": str(e),
        }


def autocorrelation_test(data_values: np.ndarray, max_lag: int = 12) -> dict[str, Any]:
    """
    Test for temporal autocorrelation using Ljung-Box test.

    Args:
        data_values: Time series data
        max_lag: Maximum lag to test

    Returns:
        Dict with test results
    """
    from statsmodels.stats.diagnostic import acorr_ljungbox

    clean_data = data_values[~np.isnan(data_values)]

    if len(clean_data) < max_lag + 2:
        return {
            "lb_stat": np.nan,
            "lb_pvalue": np.nan,
            "significant_autocorr": False,
            "max_lag_tested": min(max_lag, len(clean_data) - 1),
        }

    try:
        result = acorr_ljungbox(clean_data, lags=max_lag, return_df=True)
        # Use the last lag test
        lb_stat = result.iloc[-1]['lb_stat']
        lb_pvalue = result.iloc[-1]['lb_pvalue']

        return {
            "lb_stat": float(lb_stat),
            "lb_pvalue": float(lb_pvalue),
            "significant_autocorr": lb_pvalue < 0.05,
            "max_lag_tested": max_lag,
            "all_lags": result.to_dict('records'),
        }
    except Exception as e:
        return {
            "lb_stat": np.nan,
            "lb_pvalue": np.nan,
            "significant_autocorr": False,
            "error": str(e),
        }


def comprehensive_trend_analysis(
    data_values: np.ndarray,
    time_values: np.ndarray | None = None,
    variable: str = "unknown",
    unit: str = "unknown",
    period: int = 12,
    reference_period: tuple[int, int] | None = None
) -> dict[str, Any]:
    """
    Perform comprehensive trend analysis on a time series.

    Args:
        data_values: Time series data
        time_values: Time values (year fractions, e.g., 2000.0, 2000.0833, ...)
        variable: Variable name for metadata
        unit: Unit of measurement
        period: Seasonal period for monthly data
        reference_period: Reference period for anomalies

    Returns:
        Complete analysis results
    """
    if time_values is None:
        time_values = np.arange(len(data_values))

    # Basic statistics
    desc_stats = descriptive_statistics(data_values)

    # Linear regression
    linreg = linear_regression_analysis(time_values, data_values)

    # Mann-Kendall test
    mk_result = mann_kendall_test(data_values)

    # Seasonal Mann-Kendall for monthly data
    seasonal_mk = seasonal_mann_kendall_test(data_values, period=period)

    # Sen's slope
    sens = sens_slope(data_values, time_values)

    # Anomalies
    anomalies = compute_anomalies(data_values, time_values, reference_period)

    # Autocorrelation test
    autocorr = autocorrelation_test(data_values)

    # Seasonal decomposition
    seasonal_decomp = seasonal_decompose(data_values, time_values, period)

    # Determine overall trend direction
    trend_direction = "no_significant_trend"
    if mk_result["h"] and mk_result["trend"] == "increasing":
        trend_direction = "increasing"
    elif mk_result["h"] and mk_result["trend"] == "decreasing":
        trend_direction = "decreasing"
    elif seasonal_mk["h"] and seasonal_mk["trend"] == "increasing":
        trend_direction = "increasing"
    elif seasonal_mk["h"] and seasonal_mk["trend"] == "decreasing":
        trend_direction = "decreasing"

    # Significance
    is_significant = mk_result["h"] or seasonal_mk["h"]

    # Confidence in trend (based on multiple lines of evidence)
    evidence = []
    if mk_result["h"]:
        evidence.append(f"Mann-Kendall: {mk_result['trend']} (p={mk_result['p_value']:.4f})")
    if seasonal_mk["h"]:
        evidence.append(f"Seasonal MK: {seasonal_mk['trend']} (p={seasonal_mk['p_value']:.4f})")
    if not np.isnan(sens["slope"]):
        evidence.append(f"Sen's slope: {sens['slope']:.4f} {unit}/year")
    if not np.isnan(linreg["slope"]):
        evidence.append(f"Linear regression: {linreg['slope']:.4f} {unit}/year (p={linreg['p_value']:.4f})")

    return {
        "variable": variable,
        "unit": unit,
        "descriptive_statistics": desc_stats,
        "linear_regression": linreg,
        "mann_kendall": mk_result,
        "seasonal_mann_kendall": seasonal_mk,
        "sens_slope": sens,
        "anomalies": anomalies["anomalies"].tolist(),
        "reference_mean": anomalies["reference_mean"],
        "autocorrelation": autocorr,
        "seasonal_decomposition": {
            "trend": seasonal_decomp["trend"].tolist(),
            "seasonal": seasonal_decomp["seasonal"].tolist(),
            "residual": seasonal_decomp["residual"].tolist(),
        },
        "trend_direction": trend_direction,
        "is_significant": is_significant,
        "evidence": evidence,
        "interpretation": generate_interpretation(trend_direction, is_significant, sens, linreg, mk_result, variable, unit),
        "limitations": generate_limitations(desc_stats, autocorr, mk_result, seasonal_mk),
    }


def generate_interpretation(
    trend_direction: str,
    is_significant: bool,
    sens: dict,
    linreg: dict,
    mk: dict,
    variable: str,
    unit: str
) -> str:
    """Generate a plain-language interpretation of the trend analysis."""
    if trend_direction == "insufficient_data":
        return f"Insufficient data to determine a trend in {variable}."

    if not is_significant:
        return (
            f"No statistically significant trend detected in {variable}. "
            f"While the linear regression suggests a slope of {linreg.get('slope', np.nan):.4f} {unit}/year "
            f"(p={linreg.get('p_value', np.nan):.3f}), the Mann-Kendall test does not reject the null hypothesis "
            f"of no monotonic trend (p={mk.get('p_value', np.nan):.3f}). Observed changes may be within "
            f"natural variability."
        )

    direction_text = "increasing" if trend_direction == "increasing" else "decreasing"
    sens_slope_val = sens.get('slope', np.nan)
    linreg_slope = linreg.get('slope', np.nan)

    return (
        f"A statistically significant {direction_text} trend is detected in {variable}. "
        f"Sen's slope estimator indicates a rate of change of {sens_slope_val:.4f} {unit}/year "
        f"(95% CI: {sens.get('ci_lower', np.nan):.4f} to {sens.get('ci_upper', np.nan):.4f} {unit}/year). "
        f"Linear regression yields a similar slope of {linreg_slope:.4f} {unit}/year "
        f"(R²={linreg.get('r_squared', np.nan):.3f}, p={linreg.get('p_value', np.nan):.3f}). "
        f"The Mann-Kendall test confirms a {mk['trend']} monotonic trend (p={mk['p_value']:.4f}). "
        f"This trend is unlikely to be due to random chance alone. However, correlation does not imply causation; "
        f"the observed trend may be influenced by multiple factors including natural climate variability, "
        f"anthropogenic climate change, land use changes, or data artifacts."
    )


def generate_limitations(
    desc_stats: dict,
    autocorr: dict,
    mk: dict,
    seasonal_mk: dict
) -> list[str]:
    """Generate list of scientific limitations for the analysis."""
    limitations = []

    if desc_stats["missing_pct"] > 10:
        limitations.append(
            f"High percentage of missing data ({desc_stats['missing_pct']:.1f}%) may bias trend estimates."
        )
    elif desc_stats["missing_pct"] > 5:
        limitations.append(
            f"Moderate missing data ({desc_stats['missing_pct']:.1f}%) may affect trend reliability."
        )

    if desc_stats["n_obs"] < 30:
        limitations.append(
            f"Short time series ({desc_stats['n_obs']} observations) limits statistical power and "
            f"ability to detect long-term trends."
        )

    if autocorr.get("significant_autocorr", False):
        limitations.append(
            "Significant temporal autocorrelation detected. This can inflate significance of trend tests. "
            "Seasonal Mann-Kendall or pre-whitening methods may be more appropriate."
        )

    if not mk["h"] and seasonal_mk["h"]:
        limitations.append(
            "Standard Mann-Kendall test did not detect a trend, but Seasonal Mann-Kendall did. "
            "This suggests a seasonal pattern in the trend that the standard test may miss."
        )

    limitations.append(
        "Trend analysis assumes stationarity of statistical properties over time. "
        "Non-stationarity (e.g., changing variance) may affect results."
    )

    limitations.append(
        "Results are based on a single dataset and reanalysis/model product. "
        "Different datasets may yield different trend estimates due to varying methodologies, "
        "input observations, and model physics."
    )

    limitations.append(
        "Statistical significance does not imply practical significance. "
        "The magnitude of change should be evaluated in the context of natural variability "
        "and societal impacts."
    )

    limitations.append(
        "Causation cannot be inferred from trend detection alone. "
        "Attribution requires additional analysis with climate models and multiple lines of evidence."
    )

    return limitations


def spatial_trend_analysis(
    cell_data: list[dict],
    time_values: np.ndarray,
    variable: str,
    unit: str,
    period: int = 12
) -> list[dict]:
    """
    Perform trend analysis on each grid cell for spatial trend mapping.

    Args:
        cell_data: List of dicts with 'time_series', 'lat', 'lon', etc.
        time_values: Time values for the series
        variable: Variable name
        unit: Unit of measurement
        period: Seasonal period

    Returns:
        List of trend results per grid cell
    """
    results = []

    for cell in cell_data:
        ts = np.array(cell["time_series"])

        # Need at least some valid data
        valid_mask = ~np.isnan(ts)
        if valid_mask.sum() < 4:
            results.append({
                "lat": cell["lat"],
                "lon": cell["lon"],
                "trend_direction": "insufficient_data",
                "trend_magnitude": None,
                "p_value": None,
                "significance": False,
                "n_obs": int(valid_mask.sum()),
            })
            continue

        # Run MK test
        mk_result = mann_kendall_test(ts)

        # Sen's slope
        sens = sens_slope(ts, time_values)

        trend_dir = "no_significant_trend"
        if mk_result["h"] and mk_result["trend"] == "increasing":
            trend_dir = "increasing"
        elif mk_result["h"] and mk_result["trend"] == "decreasing":
            trend_dir = "decreasing"

        results.append({
            "lat": cell["lat"],
            "lon": cell["lon"],
            "trend_direction": trend_dir,
            "trend_magnitude": float(sens["slope"]) if not np.isnan(sens["slope"]) else None,
            "p_value": float(mk_result["p_value"]),
            "significance": mk_result["h"],
            "n_obs": int(valid_mask.sum()),
            "tau": mk_result["tau"],
            "sens_slope": sens["slope"],
            "sens_ci": [sens["ci_lower"], sens["ci_upper"]],
        })

    return results