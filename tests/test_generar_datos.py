import unittest

import numpy as np
import pandas as pd

from src.generar_datos import (
    create_branches,
    create_customers,
    create_products,
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


if __name__ == "__main__":
    unittest.main()