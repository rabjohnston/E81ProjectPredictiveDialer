from simulation import Simulation
import math
import logging as log


class SimulationAnalytic(Simulation):

    def __init__(self):
        Simulation.__init__(self, False)
        
        # We desire all agents to be utilised at all times
        self._desired_agent_occupation_rate = 1
        
        # The legal limit in a lot of countries is max abandonment rate of 5%
        self._max_abandonment_rate = 0.05
        
        self._max_traffic = 0;

        self._prob_answer = 0.36;

        self._prob_long_call = 0.22;

        self._prob_short_call = 1 - self._prob_long_call;

        self._ave_length_long_call = 430000

        self._ave_length_short_call = 180000
        
        # We assume trunks are infinite. This is valid if we have IP telephony as trunks are virtual
        self._available_trunks = 100000


    def calculate_calls(self):
        """
        Ensure the number of in progress calls match the number of free agents
        """

        number_calls_to_make = 0

        if self._current_time < self.ONE_MINUTE:
            if self._current_time % self.ONE_SECOND == 0:
                number_calls_to_make = 1
        else:
            # Tmax = N * AO
            self._max_traffic = self._number_free_agents * self._desired_agent_occupation_rate

            # Calculate probability of answer, p
            self._prob_answer = self.total_number_answered_calls /\
                                ( self.total_number_answered_calls + self.total_number_not_answered_calls)

            denom = self._prob_answer * (( self._prob_long_call / self._ave_length_long_call) +
                                             (self._prob_short_call / self._ave_length_short_call))
            calls = (self._max_traffic / denom) - self.number_ringing_calls()

            calls = min(self._available_trunks, max(0, calls))
            log.debug('calls: {}'.format(calls))



            # Calculate the optimal number of calls to launch
            if number_calls_to_make < 0:
                number_calls_to_make = 0

        return number_calls_to_make

