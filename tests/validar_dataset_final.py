from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    sales = pd.read_csv(
        DATA_DIR / "fact_ventas.csv",
        parse_dates=["fecha"],
    )
    branches = pd.read_csv(DATA_DIR / "dim_sucursal.csv")
    products = pd.read_csv(DATA_DIR / "dim_producto.csv")
    customers = pd.read_csv(DATA_DIR / "dim_cliente.csv")
    calendar = pd.read_csv(DATA_DIR / "dim_fecha.csv")

    required_columns = {
        "id_venta",
        "fecha",
        "sucursal",
        "vendedor",
        "cliente",
        "categoria",
        "producto",
        "costo",
        "precio",
        "cantidad",
        "descuento",
        "utilidad",
        "metodo_pago",
        "tiempo_entrega",
        "satisfaccion_cliente",
        "indice_macroeconomico",
        "clima",
        "dolar_paralelo",
        "nivel_trafico",
        "score_riesgo_cliente",
        "probabilidad_fuga",
        "indice_inflacion",
    }

    check(len(sales) == 5000, "Se esperaban 5.000 ventas.")
    check(required_columns.issubset(sales.columns), "Faltan columnas.")
    check(sales["id_venta"].is_unique, "id_venta debe ser único.")
    check(len(branches) == 120, "Deben existir 120 sucursales.")
    check(branches["region"].nunique() == 4, "Deben existir 4 regiones.")
    check(len(products) == 50, "Se esperaban 50 productos.")
    check(len(customers) == 1000, "Se esperaban 1.000 clientes.")
    check(len(calendar) == 1096, "El calendario debe tener 1.096 días.")

    critical_columns = [
        "fecha",
        "sucursal",
        "cliente",
        "producto",
        "costo",
        "precio",
        "cantidad",
        "utilidad",
        "probabilidad_fuga",
    ]
    check(
        not sales[critical_columns].isna().any().any(),
        "Existen nulos en columnas críticas.",
    )
    check((sales["cantidad"] > 0).all(), "Cantidad debe ser positiva.")
    check((sales["costo"] > 0).all(), "Costo debe ser positivo.")
    check((sales["precio"] > sales["costo"]).all(), "Precio debe superar costo.")
    check(sales["descuento"].between(0, 0.60).all(), "Descuento inválido.")
    check(
        sales["satisfaccion_cliente"].between(1, 5).all(),
        "Satisfacción inválida.",
    )
    check(
        sales["probabilidad_fuga"].between(0, 1).all(),
        "Probabilidad de fuga inválida.",
    )
    check(
        sales["es_outlier_simulado"].sum() == 100,
        "Se esperaban exactamente 100 outliers.",
    )

    expected_utility = (
        sales["precio"]
        * sales["cantidad"]
        * (1 - sales["descuento"])
        - sales["costo"] * sales["cantidad"]
    ).round(2)

    check(
        (expected_utility - sales["utilidad"]).abs().max() < 0.011,
        "Utilidad inconsistente con precio, costo y descuento.",
    )
    check(
        sales["nivel_trafico"].corr(sales["cantidad"]) > 0.08,
        "Tráfico debe relacionarse positivamente con cantidad.",
    )
    check(
        sales["tiempo_entrega"].corr(sales["satisfaccion_cliente"]) < -0.15,
        "Entrega debe afectar negativamente la satisfacción.",
    )

    print("OK: dataset final validado.")
    print(f"Ventas: {len(sales):,}")
    print(f"Columnas FACT_VENTAS: {len(sales.columns)}")
    print(f"Outliers: {sales['es_outlier_simulado'].sum()}")
    print(
        "Correlación tráfico-cantidad:",
        round(sales["nivel_trafico"].corr(sales["cantidad"]), 3),
    )
    print(
        "Correlación entrega-satisfacción:",
        round(
            sales["tiempo_entrega"].corr(
                sales["satisfaccion_cliente"]
            ),
            3,
        ),
    )


if __name__ == "__main__":
    main()