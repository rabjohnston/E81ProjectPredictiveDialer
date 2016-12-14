from simulation import Simulation
import logging as log


class SimulationFreeAgent(Simulation):

    def __init__(self):
        Simulation.__init__(self)


    def calculate_calls(self):
        """
        Ensure the number of in progress calls match the number of free agents
        """

        # Add up all the possible calls that could become available.
        in_progress = self.number_created_calls() + self.number_ringing_calls() + self.number_queued_calls()

        # Do we have excess agents?
        number_calls_to_make = self._number_free_agents - in_progress

        if number_calls_to_make < 0:
            number_calls_to_make = 0

        return number_calls_to_make

# INFO     Report:
# INFO       current_time:                    02:01:06.800
# INFO       number_created_calls:            0
# INFO       number_ringing_calls:            0
# INFO       number_queued_calls:             0
# INFO       number_talking_calls:            0
# INFO       number_disconnected_calls:       3966
# INFO       number_free_agents:              0
# INFO       number_busy_agents:              0
# INFO       total_number_answered_calls:     1907
# INFO       total_number_not_answered_calls: 2059
# INFO       total_number_abandon_calls:      0
# INFO       total_number_talking_calls:      1907
# INFO       total_number_calls:              3966
# INFO       total_agent_idle_time:           172745800
# INFO       total_agent_talk_time:           115778600
