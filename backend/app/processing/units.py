"""Unit checks/conversions. Unknown units are preserved, never guessed."""
def normalize_units(data_array, variable: str):
    units=data_array.attrs.get("units")
    if not units: raise ValueError(f"No source units declared for {variable}")
    data_array.attrs["original_units"]=units
    data_array.attrs["units"]=units
    data_array.attrs["unit_conversion"]="none; source units preserved"
    return data_array
