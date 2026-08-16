import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CONFIG_PATH = ROOT / "config" / "parametros.json"


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def build_inventory(
    branches: pd.DataFrame,
    products: pd.DataFrame,
    cutoff_date: pd.Timestamp,
    critical_rate: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    required_branches = {"id_sucursal"}
    required_products = {"id_producto"}

    if not required_branches.issubset(branches.columns):
        raise ValueError("dim_sucursal.csv no contiene id_sucursal.")

    if not required_products.issubset(products.columns):
        raise ValueError("dim_producto.csv no contiene id_producto.")

    if not 0 < critical_rate < 1:
        raise ValueError("inventory_critical_rate debe estar entre 0 y 1.")

    inventory = (
        branches[["id_sucursal"]]
        .merge(products[["id_producto"]], how="cross")
        .sort_values(["id_sucursal", "id_producto"])
        .reset_index(drop=True)
    )

    row_count = len(inventory)

    reorder_point = rng.integers(8, 31, size=row_count)
    is_critical = rng.random(row_count) < critical_rate

    normal_stock = reorder_point + rng.integers(8, 101, size=row_count)
    critical_stock = np.array(
        [rng.integers(0, point + 1) for point in reorder_point]
    )

    inventory["fecha_corte"] = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
    inventory["stock_actual"] = np.where(
        is_critical,
        critical_stock,
        normal_stock,
    )
    inventory["punto_reorden"] = reorder_point

    return inventory[
        [
            "fecha_corte",
            "id_sucursal",
            "id_producto",
            "stock_actual",
            "punto_reorden",
        ]
    ]


def main() -> None:
    config = load_config()

    branches = pd.read_csv(RAW_DIR / "dim_sucursal.csv")
    products = pd.read_csv(RAW_DIR / "dim_producto.csv")
    sales = pd.read_csv(RAW_DIR / "fact_ventas.csv", parse_dates=["fecha"])

    cutoff_date = sales["fecha"].max().normalize()
    critical_rate = config["simulation"].get("inventory_critical_rate", 0.08)

    rng = np.random.default_rng(config["project"]["random_seed"] + 101)

    inventory = build_inventory(
        branches=branches,
        products=products,
        cutoff_date=cutoff_date,
        critical_rate=critical_rate,
        rng=rng,
    )

    output_path = RAW_DIR / "inventario.csv"
    inventory.to_csv(output_path, index=False)

    critical_count = (
        inventory["stock_actual"] <= inventory["punto_reorden"]
    ).sum()

    print(f"Archivo: {output_path}")
    print(f"Snapshot: {cutoff_date.date()}")
    print(f"Filas: {len(inventory):,}")
    print(f"Registros críticos: {critical_count:,}")


if __name__ == "__main__":
    main()