from simulation import Simulation
import logging as log


class SimulationAnalytic(Simulation):

    def __init__(self):
        Simulation.__init__(self)
        
        # We desire all agents to be utilised at all times
        self._desired_agent_occupation_rate = 1
        
        # The legal limit in a lot of countries is max abandonment rate of 5%
        self._max_abandonment_rate = 0.05
        
        self._max_traffic = 0;

        self._prob_answer = 0;
        
        # We assume trunks are infinite. This is valid if we have IP telephony as trunks are virtual
        self._available_trunks = 100000


    def calculate_calls(self):
        """
        Ensure the number of in progress calls match the number of free agents
        """

        # Tmax = N * AO
        self._max_traffic = self._number_free_agents * self._desired_agent_occupation_rate

        # Calculate probability of answer, p
        self._prob_answer = self.total_number_answered_calls /( self.total_number_answered_calls + self.total_number_not_answered_calls)

        self._calculate_delta()

        number_calls_to_make = 0

        # Calculate the optimal number of calls to launch
        if number_calls_to_make < 0:
            number_calls_to_make = 0

        return number_calls_to_make


    def _calculate_delta(self):
        return 0