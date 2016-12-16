from unittest import TestCase
from simulation_constant_call import SimulationConstantCall


class TestSimulationConstantCall(TestCase):

    def test_constructor_default_interval(self):
        sim = SimulationConstantCall()
        self.assertEqual(sim._interval, 1000)
        self.assertEqual(sim._dial_level, 1)


    def test_constructor_calls_too_small(self):
        sim = SimulationConstantCall(-1)
        self.assertEqual(sim._interval, 1000)
        self.assertEqual(sim._dial_level, 0)


