from unittest import TestCase
from simulation_constant_call import SimulationConstantCall


class TestSimulationConstantCall(TestCase):

    def test_constructor_default_interval(self):
        sim = SimulationConstantCall()
        self.assertEqual(sim._interval, 1000)


    def test_constructor_interval_too_small(self):
        sim = SimulationConstantCall(interval=20)
        self.assertEqual(sim._interval, sim.EPOCH)


    def test_constructor_interval_not_multiple(self):
        sim = SimulationConstantCall(interval=150)
        self.assertEqual(sim._interval, sim.EPOCH)
