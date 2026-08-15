from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "parametros.json"


def load_config() -> dict:
    """Lee los parámetros versionados del proyecto."""
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def create_branches(config: dict, rng: np.random.Generator) -> pd.DataFrame:
    """
    Lognormal se usa porque el factor debe ser siempre positivo y unas pocas
    sucursales grandes deben vender más que la sucursal promedio.
    """
    regions = ["Occidente", "Valles", "Centro", "Oriente"]
    cities = {
        "Occidente": ["La Paz", "El Alto", "Oruro"],
        "Valles": ["Cochabamba", "Sucre", "Tarija"],
        "Centro": ["Potosí", "Chuquisaca", "Cochabamba Sur"],
        "Oriente": ["Santa Cruz", "Trinidad", "Cobija"],
    }

    branch_count = config["simulation"]["branches"]
    if branch_count % len(regions) != 0:
        raise ValueError("El número de sucursales debe dividirse entre las regiones.")

    rows = []
    for branch_id in range(1, branch_count + 1):
        region = regions[(branch_id - 1) % len(regions)]
        city = cities[region][(branch_id - 1) % len(cities[region])]

        rows.append(
            {
                "id_sucursal": branch_id,
                "sucursal": f"Sucursal {branch_id:03d}",
                "region": region,
                "ciudad": city,
                "factor_demanda_sucursal": round(
                    float(rng.lognormal(mean=0.0, sigma=0.20)), 4
                ),
            }
        )

    return pd.DataFrame(rows)

def create_products(rng: np.random.Generator) -> pd.DataFrame:
    """Crea productos con costo, margen y popularidad por categoría."""
    profiles = [
        ("Alimentos", 16, 8.0, 0.22, False),
        ("Bebidas", 8, 6.0, 0.24, False),
        ("Hogar", 8, 35.0, 0.28, False),
        ("Tecnología", 7, 260.0, 0.18, True),
        ("Cuidado personal", 6, 24.0, 0.30, False),
        ("Moda", 5, 75.0, 0.36, True),
    ]

    rows = []
    product_id = 1

    for category, count, base_cost, target_margin, imported in profiles:
        for sequence in range(1, count + 1):
            cost = base_cost * rng.lognormal(mean=0.0, sigma=0.25)

            rows.append(
                {
                    "id_producto": product_id,
                    "producto": f"{category} {sequence:02d}",
                    "categoria": category,
                    "costo_base": round(float(cost), 2),
                    "margen_objetivo": target_margin,
                    "importado": imported,
                    "popularidad": round(
                        float(rng.lognormal(mean=0.0, sigma=0.45)), 4
                    ),
                }
            )
            product_id += 1

    return pd.DataFrame(rows)

def create_customers(
    config: dict, rng: np.random.Generator
) -> pd.DataFrame:
    """Crea atributos latentes que impulsarán pago, churn y scoring."""
    customer_count = config["simulation"]["customers"]
    customer_ids = np.arange(1, customer_count + 1)

    risk = rng.beta(a=2.2, b=3.8, size=customer_count) * 100
    loyalty = rng.beta(a=2.8, b=2.2, size=customer_count)
    digital_preference = rng.beta(a=2.0, b=2.0, size=customer_count)
    relative_income = rng.lognormal(
        mean=0.0, sigma=0.35, size=customer_count
    )

    return pd.DataFrame(
        {
            "id_cliente": customer_ids,
            "cliente": [
                f"Cliente {customer_id:04d}"
                for customer_id in customer_ids
            ],
            "score_riesgo_cliente_base": np.round(risk, 2),
            "lealtad_latente": np.round(loyalty, 4),
            "preferencia_digital": np.round(digital_preference, 4),
            "ingreso_relativo": np.round(relative_income, 4),
        }
    )

def create_calendar_effects(
    config: dict, rng: np.random.Generator
) -> pd.DataFrame:
    """Genera tendencia, estacionalidad y contexto macro por día."""
    simulation = config["simulation"]
    dates = pd.date_range(
        simulation["start_date"],
        simulation["end_date"],
        freq="D",
    )

    day_number = np.arange(len(dates))
    day_of_year = dates.dayofyear.to_numpy()

    annual_seasonality = np.sin(
        2 * np.pi * (day_of_year - 18) / 365.25
    )
    semiannual_seasonality = np.sin(
        4 * np.pi * day_of_year / 365.25
    )
    trend = day_number / len(dates)

    inflation = (
        3.0
        + 2.5 * trend
        + 0.40 * annual_seasonality
        + rng.normal(0, 0.12, len(dates))
    )
    parallel_dollar = (
        6.90 * (1 + 0.06 * trend)
        + 0.15 * annual_seasonality
        + rng.normal(0, 0.025, len(dates))
    )
    macro_index = (
        100
        + 4.0 * annual_seasonality
        + 2.2 * semiannual_seasonality
        - 3.0 * trend
        + rng.normal(0, 0.8, len(dates))
    )
    calendar_demand = np.exp(
        0.22 * annual_seasonality
        + 0.07 * semiannual_seasonality
        + 0.04 * trend
    )

    return pd.DataFrame(
        {
            "fecha_dia": dates,
            "indice_inflacion": inflation,
            "dolar_paralelo": parallel_dollar,
            "indice_macroeconomico": macro_index,
            "demanda_calendario": calendar_demand,
        }
    )

def sample_transaction_dates(
    calendar: pd.DataFrame,
    transaction_count: int,
    rng: np.random.Generator,
) -> pd.Series:
    """Muestrea fechas según demanda y menor actividad de fin de semana."""
    weekend_factor = np.where(
        calendar["fecha_dia"].dt.dayofweek >= 5,
        0.72,
        1.0,
    )
    weights = calendar["demanda_calendario"].to_numpy() * weekend_factor
    probabilities = weights / weights.sum()

    day_positions = rng.choice(
        len(calendar),
        size=transaction_count,
        replace=True,
        p=probabilities,
    )
    sampled_days = calendar.iloc[day_positions]["fecha_dia"].reset_index(
        drop=True
    )
    seconds_open = rng.integers(
        9 * 3600,
        21 * 3600,
        size=transaction_count,
    )

    return sampled_days + pd.to_timedelta(seconds_open, unit="s")


def create_transaction_skeleton(
    config: dict,
    calendar: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    transaction_count = config["simulation"]["transaction_count"]

    return pd.DataFrame(
        {
            "id_venta": np.arange(1, transaction_count + 1),
            "fecha": sample_transaction_dates(
                calendar,
                transaction_count,
                rng,
            ),
        }
    )

def assign_transaction_entities(
    transactions: pd.DataFrame,
    branches: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Asigna entidades usando probabilidades de negocio."""
    sales = transactions.copy()
    transaction_count = len(sales)

    branch_weights = branches["factor_demanda_sucursal"].to_numpy()
    sales["id_sucursal"] = rng.choice(
        branches["id_sucursal"].to_numpy(),
        size=transaction_count,
        p=branch_weights / branch_weights.sum(),
    )

    customer_weights = 0.35 + customers["lealtad_latente"].to_numpy()
    sales["id_cliente"] = rng.choice(
        customers["id_cliente"].to_numpy(),
        size=transaction_count,
        p=customer_weights / customer_weights.sum(),
    )

    product_weights = products["popularidad"].to_numpy()
    sales["id_producto"] = rng.choice(
        products["id_producto"].to_numpy(),
        size=transaction_count,
        p=product_weights / product_weights.sum(),
    )

    sales = sales.merge(branches, on="id_sucursal", how="left")
    sales = sales.merge(customers, on="id_cliente", how="left")
    sales = sales.merge(products, on="id_producto", how="left")

    return sales

def main() -> None:
    config = load_config()
    rng = np.random.default_rng(config["project"]["random_seed"])

    branches = create_branches(config, rng)

    print(branches.head())
    print("\nSucursales por región:")
    print(branches.groupby("region").size())
    print("\nFactor de demanda:")
    print(branches["factor_demanda_sucursal"].describe())

    products = create_products(rng)

    print("\nProductos por categoría:")
    print(products.groupby("categoria").size())
    print("\nCosto base por categoría:")
    print(products.groupby("categoria")["costo_base"].mean().round(2))

    customers = create_customers(config, rng)

    print("\nPerfil de clientes:")
    print(
        customers[
            [
                "score_riesgo_cliente_base",
                "lealtad_latente",
                "preferencia_digital",
                "ingreso_relativo",
            ]
        ].describe()
    )

    calendar = create_calendar_effects(config, rng)

    print("\nCalendario:")
    print(calendar[["fecha_dia", "indice_inflacion", "dolar_paralelo"]].head())
    print(calendar.describe())

    transactions = create_transaction_skeleton(config, calendar, rng)

    print("\nEsqueleto transaccional:")
    print(transactions.head())
    print(f"Transacciones: {len(transactions)}")
    print(
        transactions.groupby(transactions["fecha"].dt.dayofweek)
        .size()
        .rename("ventas_por_dia_semana")
    )

    sales = assign_transaction_entities(
        transactions,
        branches,
        products,
        customers,
        rng,
    )

    print("\nVentas por región:")
    print(sales.groupby("region").size())
    print("\nCinco productos con más transacciones:")
    print(sales["producto"].value_counts().head())


if __name__ == "__main__":
    main()