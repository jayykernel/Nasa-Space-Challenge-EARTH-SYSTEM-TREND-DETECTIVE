"""Build plain language only from computed values and observed coverage."""
def explain(variable: str, stats: dict, unit: str) -> list[str]:
    if stats.get("status") != "completed":
        return [f"There are not enough valid observations to estimate a trend in {variable}."]
    mk=stats["mann_kendall"]; slope=stats["sens_slope"]; desc=stats["descriptive_stats"]
    if mk["p_value"] is None: return [f"A trend could not be estimated for {variable}."]
    if mk.get("significant"):
        conclusion=f"Mann–Kendall detected a statistically significant {mk['trend']} monotonic trend (p={mk['p_value']:.4g})."
    else:
        conclusion=(f"Mann–Kendall did not detect a statistically significant monotonic trend (p={mk['p_value']:.4g}); "
                    f"the estimated direction was {mk['trend']}, but the evidence is insufficient to call it a trend.")
    text=f"The regional {variable} series has {desc['n_obs']} valid observations. {conclusion}"
    if slope.get("slope") is not None:
        text += f" The estimated Sen slope is {slope['slope']:.6g} {unit} per year"
        if slope.get("ci_lower") is not None and slope.get("ci_upper") is not None:
            text += f" (95% confidence interval {slope['ci_lower']:.6g} to {slope['ci_upper']:.6g})"
        text += "."
    seasonal=stats.get("seasonal_mann_kendall",{})
    if seasonal.get("p_value") is not None:
        if seasonal.get("significant"):
            text += f" The seasonal Mann–Kendall test also detected a significant {seasonal['trend']} trend (p={seasonal['p_value']:.4g})."
        else:
            text += f" The seasonal Mann–Kendall test found no significant trend (p={seasonal['p_value']:.4g})."
    if stats.get("autocorrelation",{}).get("significant_autocorr"):
        text += " Residual serial autocorrelation was flagged and an approximate AR(1) variance correction was applied to the Mann–Kendall test."
    text += " Statistical association does not establish a cause."
    return [text]
