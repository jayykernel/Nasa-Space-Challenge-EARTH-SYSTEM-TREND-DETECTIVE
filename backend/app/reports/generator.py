"""JSON, CSV and PDF report output based solely on stored results."""
import csv, io, json

def generate_report(result: dict) -> dict:
    stats=result["trend_statistics"]; var=result["variables"][0]
    return {"title":f"Earth System Trend Investigation: {var}","investigation_id":result["investigation_id"],
            "region_description":"Selected GeoJSON region","variables":result["variables"],"dataset_info":result["dataset_metadata"],
            "time_period":f"{result['time_range']['start']} to {result['time_range']['end']}",
            "observation_count":{var:stats[var]["descriptive_stats"]["n_obs"]},"units":{var:result["units"][var]},
            "data_quality_summary":json.dumps(result["data_quality"],ensure_ascii=False),
            "trend_summary":{var:stats[var].get("trend_direction","insufficient_data")},
            "rate_of_change":{var:stats[var]["sens_slope"]["slope"]},
            "statistical_significance":{var:stats[var].get("is_significant")},
            "confidence_intervals":{var:[stats[var]["sens_slope"]["ci_lower"],stats[var]["sens_slope"]["ci_upper"]]},
            "temporal_chart_data":result["time_series"],"spatial_visualization":None,
            "interpretation":" ".join(result["insights"]),"scientific_limitations":result["limitations"],
            "data_source_citation":("NOAA Climate Data Online v2, Global Summary of the Month (GSOM), PRCP datatype."
                                    if result.get("provenance", {}).get("provider") == "noaa"
                                    else "NASA GPM IMERG Final Precipitation L3 Monthly, V07 (GPM_3IMERGM)."),
            "methodology":result["methodology"],"generated_at":result["completed_at"]}

def to_csv(result: dict) -> str:
    out=io.StringIO(); writer=csv.writer(out); writer.writerow(["time","variable","value","units"])
    var=result["variables"][0]; units=result["units"][var]
    for row in result["time_series"].get(var,[]): writer.writerow([row["timestamp"],var,row["value"],units])
    return out.getvalue()

def to_pdf(report: dict) -> bytes:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as exc: raise RuntimeError("PDF reports require the optional reportlab package") from exc
    out=io.BytesIO(); page=canvas.Canvas(out,pagesize=letter); y=750
    for line in [report["title"],f"Investigation: {report['investigation_id']}",f"Period: {report['time_period']}",
                 f"Dataset: {report['data_source_citation']}",f"Interpretation: {report['interpretation']}",
                 "Limitations:",*report["scientific_limitations"]]:
        for part in [line[i:i+100] for i in range(0,len(line),100)]:
            if y<60: page.showPage(); y=750
            page.drawString(45,y,part); y-=16
    page.save(); return out.getvalue()
