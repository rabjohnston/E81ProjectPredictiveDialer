import pandas as pd
from collections import OrderedDict

from calling_list import CallingList
from callstats import CallState
import logging as log


class Simulation:

    # The number of milliseconds between each interaction
    EPOCH = 100

    ONE_SECOND = 1000
    ONE_MINUTE = ONE_SECOND * 60
    ONE_HOUR = ONE_MINUTE * 60

    LIMIT_QUEUED_CALLS = 20
    DEFAULT_SHIFT_LENGTH = ONE_HOUR * 2
    REPORTING_INTERVAL = ONE_SECOND * 10

    # The number of milliseconds between each snapshot of the current state of the call centre
    SAVE_HISTORY_INTERVAL = ONE_MINUTE


    def __init__(self):
        self._df = {}
        self._calling_list = CallingList()

        self._number_free_agents = 0
        self._number_busy_agents = 0
        self._number_agents = 0

        self._current_talk_time = 0
        self._current_abandonment_rate = 0

        self._current_time = 0

        self._duration_shift = self.DEFAULT_SHIFT_LENGTH

        self._created_calls = OrderedDict()
        self._ringing_calls = OrderedDict()
        self._queued_calls = OrderedDict()
        self._talking_calls = OrderedDict()
        self._disconnected_calls = OrderedDict()

        # A flag to indicate that the calling list still has values
        self._still_have_calls = True

        # The number of calls where the remote end picked up
        # NB: total_number_answered_calls = total_number_talking_calls + total_number_abandon_calls
        self.total_number_answered_calls = 0

        # A subset of total_number_answered_calls - the number of calls that were answered that were transferred
        # to an agent
        self.total_number_talking_calls = 0

        # A subset of total_number_answered_calls - the number of calls where the call was dropped after the remote-end
        # picked-up
        self.total_number_abandon_calls = 0

        # All the calls that never got answered at the remote end (eg Out, Busy, etc.)
        self.total_number_not_answered_calls = 0

        # Total number of calls made (inc all outcomes)
        # NB: total_number_calls = total_number_answered_calls + total_number_not_answered_calls
        self.total_number_calls = 0

        # The total time that agents are talking (busy)
        self.total_agent_talk_time = 0

        # The total time the agents are not talking (idle)
        self.total_agent_idle_time = 0

        # A history of all checkpoints taken each epoch
        self._history = OrderedDict()

        # A flag to indicate that the shift has ended. Once the shift ends agents don't take any more calls
        # and log off
        self._shift_over = False




    def number_created_calls(self):
        return len(self._created_calls)

    def number_ringing_calls(self):
        return len(self._ringing_calls)

    def number_queued_calls(self):
        return len(self._queued_calls)

    def number_talking_calls(self):
        return len(self._talking_calls)

    def number_disconnected_calls(self):
        return len(self._disconnected_calls)

    def number_all_calls(self):
        return self.number_created_calls() + self.number_ringing_calls()  \
                + self.number_queued_calls() + self.number_talking_calls()


    def start(self, calling_list, duration_shift = DEFAULT_SHIFT_LENGTH, number_agents=40):

        log.info('Running simulation for {} mins with {} agents'.format(self.millis_to_hours(duration_shift), number_agents))

        self._number_agents = number_agents
        self._number_free_agents = number_agents
        self._calling_list = calling_list
        self._duration_shift = duration_shift

        still_going = True
        while still_going:
            self._current_time += self.EPOCH

            self.handle_shift_over()

            self._tick()

            # We finish whenever we haven't got any more calls to go and the remaining calls in the system
            # finish.
            if not self._still_have_calls or self._shift_over:
                if self.number_all_calls() == 0:
                    still_going = False

        df = pd.DataFrame.from_dict(self._history, orient='index')
        log.debug(df)
        df.to_pickle('history.pkl')

        log.info('Finished. Time is: {}'.format(self.millis_to_hours(self._current_time)))

        self.print_report()
        self.print_end_report()


    def _tick(self):

        self._update_agent_stats()

        self.handle_call_events()

        if not self._shift_over:
            self.calculate()

        if self._current_time % self.REPORTING_INTERVAL == 0:
            self.print_report()

        self._create_checkpoint()


    def calculate(self):

        calls_to_make = self.calculate_calls()
        if calls_to_make > 0:
            self._still_have_calls = self.generate_call(calls_to_make)


    def generate_call(self, number_calls=1):
        log.debug('{}: make call'.format(self.millis_to_hours(self._current_time)))
        call = None
        for i in range(0, number_calls):
            call = self._calling_list.get_call()
            if call is not None:
                self._created_calls[call.unique_id] = call
                call.dial(self._current_time)
                self.total_number_calls += 1
            else:
                log.info('No more calls')
        return call is not None


    def handle_call_events(self):
        self.handle_call_events_in(self._created_calls)
        self.handle_call_events_in(self._ringing_calls)
        self.handle_call_events_in(self._queued_calls)
        self.handle_call_events_in(self._talking_calls)


    def handle_call_events_in(self, list_events):
        for unique_id in list(list_events.keys()):
            call = list_events[unique_id]
            ev = call.next_event(self._current_time)
            if ev is not None:
                if ev.state == CallState.ringing:
                    self.handle_ringing(call)
                if ev.state == CallState.answered:
                    self.handle_answered(call)
                if ev.state == CallState.disconnected:
                    self.handle_disconnected(call)


    def handle_ringing(self, call):
        log.debug('{}: {}: ringing.'.format(self.millis_to_hours(self._current_time), call.unique_id))

        self._created_calls.pop(call.unique_id)

        self._ringing_calls[call.unique_id] = call


    def handle_answered(self, call):
        log.debug('{}: {}: answered.'.format(self.millis_to_hours(self._current_time), call.unique_id))
        self._ringing_calls.pop(call.unique_id)
        self.total_number_answered_calls += 1

        if self._number_free_agents > 0:
            self.transfer_to_agent(call)
        elif self.number_queued_calls() < self.LIMIT_QUEUED_CALLS:
            self.transfer_to_queue(call)
        else:
            # No agents and we can't queue the call - abandon it
            self._disconnected_calls[call.unique_id] = call
            self.total_number_abandon_calls += 1


    def transfer_to_queue(self, call):
        self._queued_calls[call.unique_id] = call
        call.queued(self._current_time, self._calling_list.get_queued_call())


    def transfer_to_agent(self, call):
        log.debug('{}: {}: transferred.'.format(self.millis_to_hours(self._current_time), call.unique_id))
        self._make_agent_busy()
        self._talking_calls[call.unique_id] = call
        self.total_number_talking_calls += 1
        call.talking(self._current_time)


    def handle_disconnected(self, call):
        log.debug('{}: {}: disconnected. ({})'.format(self.millis_to_hours(self._current_time), call.unique_id, call.outcome_code))

        if call.unique_id in self._created_calls:
            del(self._created_calls[call.unique_id])
            self.total_number_not_answered_calls += 1

        elif call.unique_id in self._ringing_calls:
            del(self._ringing_calls[call.unique_id])
            self.total_number_not_answered_calls += 1

        elif call.unique_id in self._queued_calls:
            # This occurs whenever the call leaves the queue - treat this as an abandoned call
            self.total_number_abandon_calls += 1
            del(self._queued_calls[call.unique_id])

        elif call.unique_id in self._talking_calls:
            del(self._talking_calls[call.unique_id])
            self.release_agent()

        self._disconnected_calls[call.unique_id] = call


    def release_agent(self):

        self.make_agent_free()

        if self.number_queued_calls() > 0:
            # Get this agent straight onto a waiting call
            _, call = self._queued_calls.popitem(last=False)
            self.transfer_to_agent(call)
        elif self._shift_over:
            self._number_free_agents -= 1
            self._number_agents -= 1


    def make_agent_free(self):
        self._number_busy_agents -= 1
        self._number_free_agents += 1


    def _make_agent_busy(self):

        if self._number_free_agents == 0:
            raise Exception('Cannot make agent busy - there are none free' )

        self._number_busy_agents += 1
        self._number_free_agents -= 1


    def _update_agent_stats(self):
        self.total_agent_talk_time += self._number_busy_agents * self.EPOCH
        self.total_agent_idle_time += self._number_free_agents * self.EPOCH

        self._current_talk_time = self.total_agent_talk_time / (self.total_agent_talk_time + self.total_agent_idle_time)
        self._current_abandonment_rate = 0 if self.total_number_answered_calls == 0 else self.total_number_abandon_calls / self.total_number_answered_calls


    def handle_shift_over(self):
        if not self._shift_over and self._current_time >= self._duration_shift:
            log.info('Shift completed. Will start to take agents off.')
            self._shift_over = True

            # We will remove all ringing calls. They haven't been answered yet so we'll
            # mark them as 'Out'
            remain_ringing_calls = list(self._ringing_calls.values())
            for call in remain_ringing_calls:
                self.handle_disconnected(call)

            remain_created_calls = list(self._created_calls.values())
            for call in remain_created_calls:
                self.handle_disconnected(call)

            # All of the idle agents can log off immediately
            self._number_agents -= self._number_free_agents
            self._number_free_agents = 0

            #for call in self._talking_calls:
            #    print('Remaining: {}'.format(call))


    def _create_checkpoint(self):

        if self._current_time % self.SAVE_HISTORY_INTERVAL == 0:

            h = {'current_time': self._current_time,
                 'number_created_calls': self.number_created_calls(),
                 'number_ringing_calls': self.number_ringing_calls(),
                 'number_queued_calls': self.number_queued_calls(),
                 'number_talking_calls': self.number_talking_calls(),
                 'number_disconnected_calls': self.number_disconnected_calls(),
                 'number_free_agents': self._number_free_agents,
                 'number_busy_agents': self._number_busy_agents,
                 'total_number_answered_calls': self.total_number_answered_calls,
                 'total_number_not_answered_calls': self.total_number_not_answered_calls,
                 'total_number_abandon_calls': self.total_number_abandon_calls,
                 'total_number_calls': self.total_number_calls,
                 'total_agent_idle_time': self.total_agent_idle_time,
                 'total_agent_talk_time': self.total_agent_talk_time,
                 'current_talk_time': self._current_talk_time,
                 'current_abandonment_rate': self._current_abandonment_rate  }
            self._history[self._current_time] = h


    def print_report(self):
        log.info('')
        log.info('Report:')
        log.info('  current_time:                    {}'.format(self.millis_to_hours(self._current_time)))
        log.info('  number_created_calls:            {}'.format(self.number_created_calls()))
        log.info('  number_ringing_calls:            {}'.format(self.number_ringing_calls()))
        log.info('  number_queued_calls:             {}'.format(self.number_queued_calls()))
        log.info('  number_talking_calls:            {}'.format(self.number_talking_calls()))
        log.info('  number_disconnected_calls:       {}'.format(self.number_disconnected_calls()))
        log.info('  number_free_agents:              {}'.format(self._number_free_agents))
        log.info('  number_busy_agents:              {}'.format(self._number_busy_agents))
        log.info('  total_number_answered_calls:     {}'.format(self.total_number_answered_calls))
        log.info('  total_number_not_answered_calls: {}'.format(self.total_number_not_answered_calls))
        log.info('  total_number_abandon_calls:      {}'.format(self.total_number_abandon_calls))
        log.info('  total_number_talking_calls:      {}'.format(self.total_number_talking_calls))
        log.info('  total_number_calls:              {}'.format(self.total_number_calls))
        log.info('  total_agent_idle_time:           {}'.format(self.total_agent_idle_time))
        log.info('  total_agent_talk_time:           {}'.format(self.total_agent_talk_time))


    def print_end_report(self):
        log.info('')
        log.info('Report:')
        log.info('  abandonment rate: {}'.format( self._current_abandonment_rate ))
        log.info('  talk time:        {:.2f}% ({:.2f} mins)'.format(self._current_talk_time, self._current_talk_time * 60))


    def millis_to_hours(self, millis):
        secs, millis = divmod(millis, 1000)
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)

        return '{:02d}:{:02d}:{:02d}.{}'.format(hours, mins, secs, millis)


    def calculate_calls(self):
        return 0



