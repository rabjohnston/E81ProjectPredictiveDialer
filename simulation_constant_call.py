
from simulation import Simulation
import logging as log


class SimulationConstantCall(Simulation):

    def __init__(self, dial_level = 1, stop_immediately_when_no_calls = False):

        Simulation.__init__(self, stop_immediately_when_no_calls)

        if dial_level < 0:
            dial_level = 0

        self._dial_level = dial_level

        self._interval = Simulation.ONE_SECOND

        self._remaining_calls_to_make = 0


    def calculate_calls(self):
        """
        Make a constant number of calls per defined interval
        """
        if self._current_time % self._interval == 0:
            calls_to_make, self._remaining_calls_to_make = divmod(self._dial_level + self._remaining_calls_to_make, 1)
            return calls_to_make
        else:
            return 0



# 1 call/s
# INFO     Report:
# INFO       current_time:                    02:02:22.400
# INFO       number_created_calls:            0
# INFO       number_ringing_calls:            0
# INFO       number_queued_calls:             0
# INFO       number_talking_calls:            0
# INFO       number_disconnected_calls:       7199
# INFO       number_free_agents:              40
# INFO       number_busy_agents:              0
# INFO       total_number_answered_calls:     3392
# INFO       total_number_not_answered_calls: 3807
# INFO       total_number_abandon_calls:      10
# INFO       total_number_talking_calls:      3382
# INFO       total_number_calls:              7199
# INFO       total_agent_idle_time:           94758200
# INFO       total_agent_talk_time:           198937800

# 2 call/s
# INFO     Report:
# INFO       current_time:                    02:03:39.400
# INFO       number_created_calls:            0
# INFO       number_ringing_calls:            0
# INFO       number_queued_calls:             0
# INFO       number_talking_calls:            0
# INFO       number_disconnected_calls:       14398
# INFO       number_free_agents:              40
# INFO       number_busy_agents:              0
# INFO       total_number_answered_calls:     6966
# INFO       total_number_not_answered_calls: 7432
# INFO       total_number_abandon_calls:      474
# INFO       total_number_talking_calls:      6492
# INFO       total_number_calls:              14398
# INFO       total_agent_idle_time:           12998900
# INFO       total_agent_talk_time:           283777100

# 3 calls/s
# INFO     Report:
# INFO       current_time:                    02:05:09.200
# INFO       number_created_calls:            0
# INFO       number_ringing_calls:            0
# INFO       number_queued_calls:             0
# INFO       number_talking_calls:            0
# INFO       number_disconnected_calls:       21597
# INFO       number_free_agents:              40
# INFO       number_busy_agents:              0
# INFO       total_number_answered_calls:     10615
# INFO       total_number_not_answered_calls: 10982
# INFO       total_number_abandon_calls:      2752
# INFO       total_number_talking_calls:      7863
# INFO       total_number_calls:              21597
# INFO       total_agent_idle_time:           13772100
# INFO       total_agent_talk_time:           286595900

# 50 calls/s
# INFO     Report:
# INFO       current_time:                    02:08:23.600
# INFO       number_created_calls:            0
# INFO       number_ringing_calls:            0
# INFO       number_queued_calls:             0
# INFO       number_talking_calls:            0
# INFO       number_disconnected_calls:       359950
# INFO       number_free_agents:              40
# INFO       number_busy_agents:              0
# INFO       total_number_answered_calls:     121619
# INFO       total_number_not_answered_calls: 238331
# INFO       total_number_abandon_calls:      113170
# INFO       total_number_talking_calls:      8449
# INFO       total_number_calls:              359950
# INFO       total_agent_idle_time:           16188200
# INFO       total_agent_talk_time:           291955800

# 50 calls/s (fix: also remove created calls at end)
# INFO     Report:
# INFO       current_time:                    02:03:26.900
# INFO       number_created_calls:            0
# INFO       number_ringing_calls:            0
# INFO       number_queued_calls:             0
# INFO       number_talking_calls:            0
# INFO       number_disconnected_calls:       359950
# INFO       number_free_agents:              40
# INFO       number_busy_agents:              0
# INFO       total_number_answered_calls:     121539
# INFO       total_number_not_answered_calls: 238411
# INFO       total_number_abandon_calls:      113151
# INFO       total_number_talking_calls:      8388
# INFO       total_number_calls:              359950
# INFO       total_agent_idle_time:           7805400
# INFO       total_agent_talk_time:           288470600

# 50 calls/s (fix: also logoff agents add end)
# INFO     Report:
# INFO       current_time:                    02:03:26.900
# INFO       number_created_calls:            0
# INFO       number_ringing_calls:            0
# INFO       number_queued_calls:             0
# INFO       number_talking_calls:            0
# INFO       number_disconnected_calls:       359950
# INFO       number_free_agents:              0
# INFO       number_busy_agents:              0
# INFO       total_number_answered_calls:     121539
# INFO       total_number_not_answered_calls: 238411
# INFO       total_number_abandon_calls:      113131
# INFO       total_number_talking_calls:      8408
# INFO       total_number_calls:              359950
# INFO       total_agent_idle_time:           1050300
# INFO       total_agent_talk_time:           289400100


# INFO     Report:
# INFO       current_time:                    02:03:25.800
# INFO       number_created_calls:            0
# INFO       number_ringing_calls:            0
# INFO       number_queued_calls:             0
# INFO       number_talking_calls:            0
# INFO       number_disconnected_calls:       359995
# INFO       number_free_agents:              0
# INFO       number_busy_agents:              0
# INFO       total_number_answered_calls:     121546
# INFO       total_number_not_answered_calls: 238449
# INFO       total_number_abandon_calls:      113138
# INFO       total_number_talking_calls:      8408
# INFO       total_number_calls:              359995
# INFO       total_agent_idle_time:           1030900
# INFO       total_agent_talk_time:           289405700
