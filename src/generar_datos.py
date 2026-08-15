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


if __name__ == "__main__":
    main()