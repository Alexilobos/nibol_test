from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    inventory = pd.read_csv(
        RAW_DIR / "inventario.csv",
        parse_dates=["fecha_corte"],
    )
    branches = pd.read_csv(RAW_DIR / "dim_sucursal.csv")
    products = pd.read_csv(RAW_DIR / "dim_producto.csv")
    sales = pd.read_csv(RAW_DIR / "fact_ventas.csv", parse_dates=["fecha"])

    expected_rows = len(branches) * len(products)
    critical = inventory["stock_actual"] <= inventory["punto_reorden"]

    check(len(inventory) == expected_rows, "Cantidad de snapshots incorrecta.")
    check(
        not inventory.duplicated(
            ["fecha_corte", "id_sucursal", "id_producto"]
        ).any(),
        "Existen snapshots duplicados.",
    )
    check((inventory["stock_actual"] >= 0).all(), "Hay stock negativo.")
    check((inventory["punto_reorden"] > 0).all(), "Hay punto de reorden inválido.")
    check(critical.any(), "No se generaron registros críticos.")
    check(
        inventory["fecha_corte"].nunique() == 1,
        "El archivo debe representar un único snapshot.",
    )
    check(
        inventory["fecha_corte"].iloc[0].normalize()
        == sales["fecha"].max().normalize(),
        "La fecha de corte no coincide con el último día de ventas.",
    )

    print(
        f"OK: {len(inventory):,} snapshots, "
        f"{critical.sum():,} críticos, "
        f"fecha {inventory['fecha_corte'].iloc[0].date()}."
    )


if __name__ == "__main__":
    main()