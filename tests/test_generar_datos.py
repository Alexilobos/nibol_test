import unittest

import numpy as np
import pandas as pd

from src.generar_datos import create_branches, load_config


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


if __name__ == "__main__":
    unittest.main()