import unittest

import numpy as np
import pandas as pd

from src.generar_datos import (
    add_churn_signals,
    add_customer_experience,
    add_market_context,
    add_pricing,
    add_transaction_outcomes,
    assign_transaction_entities,
    create_branches,
    create_calendar_effects,
    create_customers,
    create_products,
    create_transaction_skeleton,
    load_config,
)
class TestBranches(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_branch_structure(self):
        rng = np.random.default_rng(self.config["project"]["random_seed"])
        branches = create_branches(self.config, rng)

        self.assertEqual(len(branches), 120)
        self.assertEqual(branches["region"].nunique(), 4)
        self.assertTrue((branches["factor_demanda_sucursal"] > 0).all())

    def test_generation_is_reproducible(self):
        seed = self.config["project"]["random_seed"]
        first = create_branches(self.config, np.random.default_rng(seed))
        second = create_branches(self.config, np.random.default_rng(seed))

        pd.testing.assert_frame_equal(first, second)

    def test_product_structure(self):
        rng = np.random.default_rng(self.config["project"]["random_seed"])
        products = create_products(rng)

        self.assertEqual(len(products), 50)
        self.assertEqual(products["categoria"].nunique(), 6)
        self.assertTrue(products["id_producto"].is_unique)
        self.assertTrue((products["costo_base"] > 0).all())
        self.assertTrue((products["popularidad"] > 0).all())
        self.assertEqual(products["importado"].sum(), 12)

    def test_customer_structure(self):
        rng = np.random.default_rng(self.config["project"]["random_seed"])
        customers = create_customers(self.config, rng)

        self.assertEqual(len(customers), 1000)
        self.assertTrue(customers["id_cliente"].is_unique)
        self.assertTrue(
            customers["score_riesgo_cliente_base"].between(0, 100).all()
        )
        self.assertTrue(customers["lealtad_latente"].between(0, 1).all())
        self.assertTrue(
            customers["preferencia_digital"].between(0, 1).all()
        )
        self.assertTrue((customers["ingreso_relativo"] > 0).all())

    def test_calendar_effects(self):
        rng = np.random.default_rng(self.config["project"]["random_seed"])
        calendar = create_calendar_effects(self.config, rng)

        self.assertEqual(len(calendar), 1096)
        self.assertEqual(calendar["fecha_dia"].min(), pd.Timestamp("2023-01-01"))
        self.assertEqual(calendar["fecha_dia"].max(), pd.Timestamp("2025-12-31"))
        self.assertTrue((calendar["indice_inflacion"] > 0).all())
        self.assertTrue((calendar["dolar_paralelo"] > 0).all())
        self.assertTrue((calendar["demanda_calendario"] > 0).all())
        self.assertGreater(calendar["demanda_calendario"].std(), 0)

    def test_transaction_skeleton(self):
        rng = np.random.default_rng(self.config["project"]["random_seed"])
        calendar = create_calendar_effects(self.config, rng)
        transactions = create_transaction_skeleton(self.config, calendar, rng)

        self.assertEqual(len(transactions), 5000)
        self.assertTrue(transactions["id_venta"].is_unique)
        self.assertGreaterEqual(transactions["fecha"].dt.hour.min(), 9)
        self.assertLessEqual(transactions["fecha"].dt.hour.max(), 20)

        weekday_count = (
            transactions["fecha"].dt.dayofweek < 5
        ).sum()
        weekend_count = (
            transactions["fecha"].dt.dayofweek >= 5
        ).sum()

        self.assertLess(weekend_count / 2, weekday_count / 5)

    def test_transaction_entity_assignment(self):
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

        required_columns = [
            "sucursal",
            "region",
            "cliente",
            "producto",
            "categoria",
        ]

        self.assertEqual(len(sales), 5000)
        self.assertFalse(sales[required_columns].isna().any().any())
        self.assertEqual(sales["region"].nunique(), 4)
        self.assertEqual(sales["sucursal"].nunique(), 120)

    def test_market_context(self):
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

        required_columns = [
            "indice_inflacion",
            "dolar_paralelo",
            "indice_macroeconomico",
            "clima",
            "nivel_trafico",
        ]

        self.assertFalse(sales[required_columns].isna().any().any())
        self.assertTrue((sales["nivel_trafico"] >= 20).all())

        rain_traffic = sales.loc[
            sales["clima"].eq("Lluvioso"),
            "nivel_trafico",
        ].mean()
        dry_traffic = sales.loc[
            ~sales["clima"].eq("Lluvioso"),
            "nivel_trafico",
        ].mean()

        self.assertLess(rain_traffic, dry_traffic)

    def test_pricing(self):
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

        self.assertFalse(
            sales[["costo", "precio", "descuento"]].isna().any().any()
        )
        self.assertTrue((sales["costo"] > 0).all())
        self.assertTrue((sales["precio"] > sales["costo"]).all())
        self.assertTrue(sales["descuento"].between(0, 0.60).all())

        campaign_discount = sales.loc[
            sales["fecha"].dt.month.isin([6, 11, 12]),
            "descuento",
        ].mean()
        regular_discount = sales.loc[
            ~sales["fecha"].dt.month.isin([6, 11, 12]),
            "descuento",
        ].mean()

        self.assertGreater(campaign_discount, regular_discount)

    def test_transaction_outcomes(self):
        sales, rng = self.build_priced_sales()
        sales = add_transaction_outcomes(sales, self.config, rng)

        expected_outliers = int(
            self.config["simulation"]["transaction_count"]
            * self.config["simulation"]["outlier_rate"]
        )
        expected_income = (
            sales["precio"]
            * sales["cantidad"]
            * (1 - sales["descuento"])
        ).round(2)
        expected_profit = (
            expected_income - sales["costo"] * sales["cantidad"]
        ).round(2)

        self.assertTrue((sales["cantidad"] > 0).all())
        self.assertEqual(
            sales["es_outlier_simulado"].sum(),
            expected_outliers,
        )
        self.assertGreater(sales["cantidad"].var(), sales["cantidad"].mean())
        self.assertGreater(sales["nivel_trafico"].corr(sales["cantidad"]), 0.08)
        self.assertLess(
            (expected_income - sales["ingreso_neto"]).abs().max(),
            0.011,
        )
        self.assertLess(
            (expected_profit - sales["utilidad"]).abs().max(),
            0.011,
        )

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

    def test_customer_experience(self):
        sales, rng = self.build_priced_sales()
        sales = add_customer_experience(sales, rng)

        self.assertTrue(sales["tiempo_entrega"].between(1, 10).all())
        self.assertTrue(
            sales["satisfaccion_cliente"].between(1, 5).all()
        )
        self.assertTrue(
            sales["score_riesgo_cliente"].between(1, 99).all()
        )

        expected_methods = {
            "Crédito",
            "Billetera digital",
            "Efectivo/Tarjeta",
        }
        self.assertEqual(
            set(sales["metodo_pago"].unique()),
            expected_methods,
        )
        self.assertLess(
            sales["tiempo_entrega"].corr(
                sales["satisfaccion_cliente"]
            ),
            -0.15,
        )

    def test_churn_signals(self):
        sales, rng = self.build_priced_sales()
        sales = add_customer_experience(sales, rng)
        sales = add_churn_signals(sales, rng)

        self.assertTrue(
            sales["probabilidad_fuga"].between(0, 1).all()
        )
        self.assertTrue(
            sales["compras_previas_cliente"].ge(0).all()
        )
        self.assertTrue(
            set(sales["fuga_real_90d"].unique()).issubset({0, 1})
        )

        low_satisfaction_churn = sales.loc[
            sales["satisfaccion_cliente"].eq(1),
            "probabilidad_fuga",
        ].mean()
        high_satisfaction_churn = sales.loc[
            sales["satisfaccion_cliente"].eq(5),
            "probabilidad_fuga",
        ].mean()

        self.assertGreater(
            low_satisfaction_churn,
            high_satisfaction_churn,
        )


if __name__ == "__main__":
    unittest.main()