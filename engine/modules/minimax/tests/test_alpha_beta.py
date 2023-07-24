import unittest
import numpy as np
from group3.engine.modules.minimax.alpha_beta import is_terminal


class TestAlphaBeta(unittest.TestCase):

    def test_is_terminal(self):
        cop_positions = [0, 3, 5]
        robber_position = 1

        self.assertTrue(not is_terminal(cop_positions, robber_position))

        robber_position = 0

        self.assertTrue(is_terminal(cop_positions, robber_position))
