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

        # The paper seems to limit the trunks to double the number of agents
        self._max_trunks = 120





    def recalc_dial_level(self):
        """
        Ensure the number of in progress calls match the number of free agents
        """

        number_calls_to_make = 0

        if self._current_time < self.ONE_MINUTE:
            if self._current_time % self.ONE_SECOND == 0:
                number_calls_to_make = 1
        elif self._current_abandonment_rate > self._max_abandonment_rate:
            number_calls_to_make = 0
        else:
            # Tmax = N * AO
            self._max_traffic = self._number_free_agents * self._desired_agent_occupation_rate

            # Calculate probability of answer, p
            self._prob_answer = self.total_number_answered_calls / self.total_number_calls

            ave_length_call = (self.total_agent_talk_time / 1000) / self.total_number_talking_calls

            denom = self._prob_answer * ave_length_call

            # denom = self._prob_answer * (( self._prob_long_call / self._ave_length_long_call) +
            #                                  (self._prob_short_call / self._ave_length_short_call))

            calls = (self._max_traffic / denom) - (self.number_ringing_calls() + self.number_created_calls())

            available_trunks = self._max_trunks - self.number_trunks_in_use()

            number_calls_to_make = min(available_trunks, max(0, calls))
            log.debug('calls: {}'.format(number_calls_to_make))



            # Calculate the optimal number of calls to launch
            if number_calls_to_make < 0:
                number_calls_to_make = 0

        return math.floor(number_calls_to_make)

