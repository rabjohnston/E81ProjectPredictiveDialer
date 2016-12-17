from unittest import TestCase
from simulation_genetic import SimulationGenetic


class TestSimulationConstantCall(TestCase):

    def test_initial_population(self):
        sim = SimulationGenetic()

        pop = sim.get_initial_population(4, 11)

        self.assertEquals(len(pop) == 11)






