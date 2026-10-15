"""Years to save a 20% down payment, core county of 50 big US metros.

Home value: Zillow Home Value Index (ZHVI, all homes, mid-tier, smoothed, SA), county, annual average.
Income: Census SAIPE median household income, county (via FRED), same year.
Years = 20% of home value / (15% of income). No investment growth, no raises, no price growth (stated).
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(os.path.dirname(HERE)), "data")
SAVE_RATE, DOWN = 0.15, 0.20


def load(year=2024, then=2000):
    cities = pd.read_csv(os.path.join(HERE, "cities.csv"), dtype={"fips": str})
    z = pd.read_csv(os.path.join(DATA, "zhvi_county.csv"), dtype={"StateCodeFIPS": str, "MunicipalCodeFIPS": str})
    z["fips"] = z.StateCodeFIPS.str.zfill(2) + z.MunicipalCodeFIPS.str.zfill(3)
    datecols = [c for c in z.columns if c[:2] in ("19", "20")]
    rows = []
    for _, c in cities.iterrows():
        zr = z[z.fips == c.fips]
        assert len(zr) == 1, c.city
        zr = zr.iloc[0]
        val = lambda y: zr[[d for d in datecols if d.startswith(str(y))]].astype(float).mean()
        inc = pd.read_csv(os.path.join(DATA, "saipe", f"MHI{c.state}{c.fips}A052NCEN.csv"), parse_dates=["observation_date"])
        inc = inc.set_index(inc.observation_date.dt.year).iloc[:, 1].astype(float)
        rows.append(dict(city=c.city, county=c.county, state=c.state, value=val(year), income=inc.get(year),
                         value_then=val(then), income_then=inc.get(then)))
    df = pd.DataFrame(rows)
    yrs = lambda v, i: DOWN * v / (SAVE_RATE * i)
    df["years"] = yrs(df.value, df.income)
    df["years_then"] = yrs(df.value_then, df.income_then)
    df["years_10"] = yrs(df.value, df.income) / 2
    df["ratio"] = df.value / df.income
    return df.sort_values("years").reset_index(drop=True)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    df = load()
    print(df.round(1).to_string())
    print("median years now", df.years.median(), "then", df.years_then.median())
