
class HistoricalEntry:

    def __init__(self, current_time, number_created_calls, number_ringing_calls, number_queued_calls,
                 number_talking_calls, number_disconnected_calls, number_free_agents,
                 number_busy_agents, total_number_answered_calls, total_number_abandon_calls, total_number_calls):

        self._number_free_agents = number_free_agents
        self._number_busy_agents = number_busy_agents

        self._total_number_answered_calls = total_number_answered_calls
        self._total_number_abandon_calls = total_number_abandon_calls
        self._total_number_calls = total_number_calls

        self._current_time = current_time

        self._number_created_calls = number_created_calls
        self._number_ringing_calls = number_ringing_calls
        self._number_queued_calls = number_queued_calls
        self._number_talking_calls = number_talking_calls
        self._number_disconnected_calls = number_disconnected_calls



