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

def add_market_context(
    sales: pd.DataFrame,
    calendar: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Añade contexto macroeconómico, clima y tráfico a cada venta."""
    result = sales.copy()
    result["fecha_dia"] = result["fecha"].dt.normalize()

    result = result.merge(
        calendar,
        on="fecha_dia",
        how="left",
    )

    climate_by_region = {
        "Occidente": "Frío",
        "Valles": "Templado",
        "Centro": "Lluvioso",
        "Oriente": "Cálido",
    }

    rain_probability = np.where(
        result["region"].eq("Centro"),
        0.45,
        0.25,
    )
    rainy = rng.random(len(result)) < rain_probability

    result["clima"] = np.where(
        rainy,
        "Lluvioso",
        result["region"].map(climate_by_region),
    )

    climate_traffic_effect = np.where(rainy, -9.0, 3.0)
    traffic = (
        100
        * result["factor_demanda_sucursal"].to_numpy()
        * result["demanda_calendario"].to_numpy()
        + climate_traffic_effect
        + rng.normal(0, 9, len(result))
    )

    result["nivel_trafico"] = np.maximum(
        20,
        np.round(traffic, 2),
    )

    return result

def add_pricing(
    sales: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Calcula costo, precio y descuento desde variables económicas."""
    result = sales.copy()

    inflation_factor = (
        1
        + (result["indice_inflacion"].to_numpy() - 3.0) / 100
    )
    import_factor = (
        1
        + result["importado"].to_numpy()
        * (result["dolar_paralelo"].to_numpy() / 6.90 - 1)
    )
    cost_noise = rng.lognormal(
        mean=0.0,
        sigma=0.05,
        size=len(result),
    )

    result["costo"] = np.round(
        result["costo_base"].to_numpy()
        * inflation_factor
        * import_factor
        * cost_noise,
        2,
    )

    target_margin = np.clip(
        result["margen_objetivo"].to_numpy()
        + rng.normal(0, 0.025, len(result)),
        0.08,
        0.65,
    )

    result["precio"] = np.round(
        result["costo"].to_numpy() / (1 - target_margin),
        2,
    )

    discount = rng.beta(1.5, 7.0, len(result)) * 0.45
    campaign_month = result["fecha"].dt.month.isin([6, 11, 12]).to_numpy()

    discount += campaign_month * rng.uniform(
        0.03,
        0.12,
        len(result),
    )

    result["descuento"] = np.round(
        np.clip(discount, 0, 0.60),
        4,
    )

    return result

def add_transaction_outcomes(
    sales: pd.DataFrame,
    config: dict,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Genera cantidad, ingresos, utilidad y outliers controlados."""
    result = sales.copy()

    expected_units = (
        1.2
        + 0.017 * result["nivel_trafico"].to_numpy()
        + 1.6 * result["descuento"].to_numpy()
        + 0.55 * result["lealtad_latente"].to_numpy()
        - 0.0018 * result["precio"].to_numpy()
    )
    expected_units = np.clip(expected_units, 0.35, 9.0)

    dispersion = 2.6
    probability = dispersion / (dispersion + expected_units)

    result["cantidad"] = (
        rng.negative_binomial(dispersion, probability) + 1
    )

    result["es_outlier_simulado"] = 0
    outlier_count = int(
        round(
            len(result)
            * config["simulation"]["outlier_rate"]
        )
    )
    outlier_index = rng.choice(
        result.index.to_numpy(),
        size=outlier_count,
        replace=False,
    )

    result.loc[outlier_index, "cantidad"] *= rng.integers(
        4,
        10,
        size=outlier_count,
    )
    result.loc[outlier_index, "descuento"] = np.round(
        rng.uniform(0.40, 0.60, size=outlier_count),
        4,
    )
    result.loc[outlier_index, "es_outlier_simulado"] = 1

    result["ingreso_neto"] = np.round(
        result["precio"]
        * result["cantidad"]
        * (1 - result["descuento"]),
        2,
    )
    result["utilidad"] = np.round(
        result["ingreso_neto"]
        - result["costo"] * result["cantidad"],
        2,
    )

    return result

def build_priced_sales(self):
    rng = np.random.default_rng(self.config["project"]["random_seed"])

    branches = create_branches(self.config, rng)
    products = create_products(rng)
    customers = create_customers(self.config, rng)
    calendar = create_calendar_effects(self.config, rng)
    transactions = create_transaction_skeleton(
        self.config,
        calendar,
        rng,
    )
    sales = assign_transaction_entities(
        transactions,
        branches,
        products,
        customers,
        rng,
    )
    sales = add_market_context(sales, calendar, rng)
    sales = add_pricing(sales, rng)

    return sales, rng

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

    sales = add_market_context(sales, calendar, rng)

    print("\nTráfico promedio por clima:")
    print(sales.groupby("clima")["nivel_trafico"].mean().round(2))
    print("\nVariables macro nulas:")
    print(
        sales[
            [
                "indice_inflacion",
                "dolar_paralelo",
                "indice_macroeconomico",
            ]
        ].isna().sum()
    )

    sales = add_pricing(sales, rng)

    print("\nPrecio y costo por categoría:")
    print(
        sales.groupby("categoria")[["costo", "precio", "descuento"]]
        .mean()
        .round(2)
    )

    sales = add_transaction_outcomes(sales, config, rng)

    print("\nResultados transaccionales:")
    print(
        sales[
            [
                "cantidad",
                "ingreso_neto",
                "utilidad",
                "es_outlier_simulado",
            ]
        ].describe()
    )
    print(
        "Tasa de outliers:",
        round(sales["es_outlier_simulado"].mean(), 4),
    )
    print(
        "Correlación tráfico-cantidad:",
        round(sales["nivel_trafico"].corr(sales["cantidad"]), 3),
    )
    print(
        "Ventas con utilidad negativa:",
        int((sales["utilidad"] < 0).sum()),
    )


if __name__ == "__main__":
    main()