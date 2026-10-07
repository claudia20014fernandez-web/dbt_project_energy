"""
Genera datos SINTÉTICOS de consumo energético y los carga en DuckDB (schema `raw`).
 
Simula lo que haría una herramienta de ingesta (el "EL" de ELT): dejar los datos
tal cual llegan, con sus problemas, para que dbt los transforme después.
 
Uso:
    python scripts/load_raw_data.py                     # carga inicial (1 ene - 31 mar 2026)
    python scripts/load_raw_data.py --append            # añade el día siguiente
    python scripts/load_raw_data.py --update-buildings  # cambia edificios (snapshots)
"""
import argparse
import random
from datetime import date, datetime, timedelta
 
import duckdb
 
DB_PATH = "energy.duckdb"
START = date(2026, 1, 1)
END = date(2026, 3, 31)
 
BUILDINGS = [
    # id, nombre, ciudad, tipo, m2, grupo propietario
    ("B01", "Torre Castellana", "Madrid", "office", 12000, "Grupo Alfa"),
    ("B02", "Centro Comercial Sol", "Madrid", "retail", 18000, "Grupo Alfa"),
    ("B03", "Residencial Retiro", "Madrid", "residential", 9000, "Grupo Beta"),
    ("B04", "Oficinas Diagonal", "Barcelona", "office", 8000, "Grupo Beta"),
    ("B05", "Nave Logistica Zona Franca", "Barcelona", "logistics", 25000, "Grupo Gamma"),
    ("B06", "Parc Comercial Mar", "Barcelona", "retail", 14000, "Grupo Gamma"),
    ("B07", "Residencial Turia", "Valencia", "residential", 11000, "Grupo Beta"),
    ("B08", "Oficinas Puerto", "Valencia", "office", 6500, "Grupo Alfa"),
    ("B09", "Nave Logistica Sevilla Este", "Sevilla", "logistics", 22000, "Grupo Gamma"),
    ("B10", "Galeria Triana", "Sevilla", "retail", 7000, "Grupo Alfa"),
    ("B11", "Torre Abando", "Bilbao", "office", 10000, "Grupo Beta"),
    ("B12", "Residencial Ria", "Bilbao", "residential", 8500, "Grupo Gamma"),
]
 
# Contadores: todos tienen electricidad; algunos también gas
METERS = []
for i, b in enumerate(BUILDINGS, start=1):
    METERS.append((f"M{i:03d}", b[0], "electricity", "2024-01-01"))
for j, b_id in enumerate(["B03", "B04", "B07", "B08", "B11", "B12"], start=13):
    METERS.append((f"M{j:03d}", b_id, "gas", "2024-01-01"))
 
TARIFFS = [
    # energy_type, valid_from, valid_to, price_eur_kwh
    ("electricity", "2026-01-01", "2026-01-31", 0.145),
    ("electricity", "2026-02-01", "2026-03-31", 0.132),
    ("electricity", "2026-04-01", None, 0.128),
    ("gas", "2026-01-01", "2026-02-28", 0.062),
    ("gas", "2026-03-01", None, 0.055),
]
 
TYPE_FACTOR = {"office": 0.030, "retail": 0.040, "residential": 0.020, "logistics": 0.018}
 
 
def hour_shape(building_type, hour, weekend):
    if building_type == "office":
        base = 1.0 if 8 <= hour <= 19 else 0.25
        return base * (0.4 if weekend else 1)
    if building_type == "retail":
        return 1.0 if 10 <= hour <= 21 else 0.2
    if building_type == "residential":
        return 1.0 if hour in (7, 8, 19, 20, 21, 22) else 0.45
    return 1.0 if 6 <= hour <= 22 else 0.3  # logistics
 
 
def make_readings(day_from, day_to, rng):
    """Devuelve filas de lecturas horarias, incluyendo problemas de calidad plantados."""
    btype = {b[0]: b[3] for b in BUILDINGS}
    area = {b[0]: b[4] for b in BUILDINGS}
    rows = []
    d = day_from
    while d <= day_to:
        weekend = d.weekday() >= 5
        for meter_id, building_id, energy_type, _ in METERS:
            for hour in range(24):
                ts = datetime(d.year, d.month, d.day, hour)
                shape = hour_shape(btype[building_id], hour, weekend)
                kwh = area[building_id] * TYPE_FACTOR[btype[building_id]] * shape
                if energy_type == "gas":
                    winter = {1: 1.3, 2: 1.0, 3: 0.7}.get(d.month, 0.4)
                    kwh *= 0.6 * winter
                kwh = round(kwh * rng.uniform(0.9, 1.1), 3)
                loaded_at = ts + timedelta(hours=1)
                rows.append([meter_id, ts, kwh, loaded_at])
        d += timedelta(days=1)
 
    n = len(rows)
    # 1) valores nulos (~0.5 %)
    for i in rng.sample(range(n), int(n * 0.005)):
        rows[i][2] = None
    # 2) valores negativos (~0.3 %)
    for i in rng.sample(range(n), int(n * 0.003)):
        if rows[i][2] is not None:
            rows[i][2] = -abs(rows[i][2])
    # 3) duplicados re-cargados al día siguiente, con valor corregido (~1 %)
    dups = []
    for i in rng.sample(range(n), int(n * 0.01)):
        meter_id, ts, kwh, loaded_at = rows[i]
        new_kwh = None if kwh is None else round(abs(kwh) * rng.uniform(0.97, 1.03), 3)
        dups.append([meter_id, ts, new_kwh, loaded_at + timedelta(days=1)])
    rows.extend(dups)
    # 4) lecturas de un contador que no existe (huérfanas)
    for _ in range(20):
        ts = datetime(day_from.year, day_from.month, day_from.day, rng.randint(0, 23))
        rows.append(["M999", ts, round(rng.uniform(1, 50), 3), ts + timedelta(hours=1)])
    return rows
 
 
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--append", action="store_true", help="añade el día siguiente")
    parser.add_argument("--update-buildings", action="store_true", help="modifica edificios")
    args = parser.parse_args()
 
    con = duckdb.connect(DB_PATH)
    con.execute("create schema if not exists raw")
 
    if args.update_buildings:
        con.execute("update raw.buildings set owner_group = 'Grupo Delta' where building_id = 'B03'")
        con.execute("update raw.buildings set area_m2 = 13500 where building_id = 'B01'")
        print("Edificios actualizados: B03 cambia de grupo propietario, B01 cambia de superficie.")
        return
 
    if args.append:
        last = con.execute("select max(reading_ts)::date from raw.meter_readings").fetchone()[0]
        next_day = last + timedelta(days=1)
        rng = random.Random(next_day.toordinal())
        rows = make_readings(next_day, next_day, rng)
        con.executemany("insert into raw.meter_readings values (?, ?, ?, ?)", rows)
        print(f"Añadido el día {next_day}: {len(rows)} filas.")
        return
 
    # --- Carga inicial ---
    rng = random.Random(42)
    con.execute("""
        create or replace table raw.buildings (
            building_id varchar, name varchar, city varchar,
            building_type varchar, area_m2 integer, owner_group varchar)
    """)
    con.executemany("insert into raw.buildings values (?, ?, ?, ?, ?, ?)", BUILDINGS)
 
    con.execute("""
        create or replace table raw.meters (
            meter_id varchar, building_id varchar, energy_type varchar, installed_at varchar)
    """)
    con.executemany("insert into raw.meters values (?, ?, ?, ?)", METERS)
 
    con.execute("""
        create or replace table raw.tariffs (
            energy_type varchar, valid_from varchar, valid_to varchar, price_eur_kwh double)
    """)
    con.executemany("insert into raw.tariffs values (?, ?, ?, ?)", TARIFFS)
 
    con.execute("""
        create or replace table raw.meter_readings (
            meter_id varchar, reading_ts timestamp, kwh double, loaded_at timestamp)
    """)
    rows = make_readings(START, END, rng)
    con.executemany("insert into raw.meter_readings values (?, ?, ?, ?)", rows)
    print(
        f"Carga inicial completada: {len(rows)} lecturas, "
        f"{len(METERS)} contadores, {len(BUILDINGS)} edificios."
    )
 
 
if __name__ == "__main__":
    main()
