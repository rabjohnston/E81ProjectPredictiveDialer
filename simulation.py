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

    MAX_CALLS_TO_GENERATE = 100

    def __init__(self, stop_immediately_when_no_calls, number_agents=40):
        self._df = {}
        self._calling_list = None

        self._number_agents = number_agents
        self._number_free_agents = number_agents
        self._number_busy_agents = 0

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

        # The legal limit in a lot of countries is max abandonment rate of 5%
        self.max_abandonment_rate = 0.05

        self.stop_immediately_when_no_calls = stop_immediately_when_no_calls

        # The number of calls to make per second. If fractional then the remainder will be saved for the next epoch
        self._dial_level = 1

        self._dial_level_recalc_period = Simulation.ONE_MINUTE

        self._fractional_call = 0

        # We'll not let the dial level get above a certain level
        self.max_dial_level = number_agents / 4






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

    def number_in_progress_calls(self):
        return self.number_created_calls() + self.number_ringing_calls()

    def number_all_calls(self):
        return self.number_created_calls() + self.number_ringing_calls()  \
                + self.number_queued_calls() + self.number_talking_calls()

    def number_trunks_in_use(self):
        return self.number_created_calls() + self.number_queued_calls() + self.number_talking_calls() + self.number_ringing_calls()

    def start(self, calling_list, duration_shift = DEFAULT_SHIFT_LENGTH):

        log.info('Running simulation for {} mins with {} agents'.format(self.millis_to_hours(duration_shift),
                                                                        self._number_agents))
        log.debug('stop_immediately set to {}'.format(self.stop_immediately_when_no_calls))

        self._calling_list = calling_list
        self._duration_shift = duration_shift

        still_going = True
        while still_going:
            self._current_time += self.EPOCH

            self.handle_shift_over()

            self._tick()

            # We finish whenever we haven't got any more calls to go and the remaining calls in the system
            # finish.
            if self.dialer_stopping():
                if self.stop_immediately_when_no_calls or (self.number_all_calls() == 0):
                    still_going = False

        df = pd.DataFrame.from_dict(self._history, orient='index')
        log.debug(df)
        df.to_pickle('history.pkl')

        log.info('Finished. Time is: {}'.format(self.millis_to_hours(self._current_time)))

        self.print_report()
        self.print_end_report()


    def dialer_stopping(self):
        """
        The dialer begins to stop whenever there are no calls left or the shift is over.
        Note: we can't stop straight away as we have calls in progress that we need to complete.
        :return:
        """
        return not self._still_have_calls or self._shift_over


    def _tick(self):

        self._update_agent_stats()

        self.handle_call_events()

        if not self._shift_over:
            self.calculate()

        if self._current_time % self.REPORTING_INTERVAL == 0:
            self.print_report()

        self._create_checkpoint()


    def calculate(self):

        if self._current_time % self._dial_level_recalc_period == 0:
            self._dial_level = self.recalc_dial_level()

        if self._current_time % Simulation.ONE_SECOND == 0:
            calls_to_make, self._fractional_call = divmod(self._dial_level + self._fractional_call, 1)
            if calls_to_make > 0:

                # Make sure the algorithm doesn't give us back something bizarre. This may happen at the beginning of
                # the shift while some algorithms are still trying to get some data.
                calls_to_make = min(self.MAX_CALLS_TO_GENERATE, calls_to_make)

                self._still_have_calls = self.generate_call(calls_to_make)


    def generate_call(self, number_calls=1):
        #log.debug('{}: make call'.format(self.millis_to_hours(self._current_time)))
        call = None
        for i in range(0, int(number_calls)):
            call = self.get_next_calling_list_entry(call)
            if call is not None:
                log.debug('{}: make call: {}, outcome: {}'.format(self.millis_to_hours(self._current_time), call.unique_id, call.outcome_code))
                self._created_calls[call.unique_id] = call
                call.dial(self._current_time)
                self.total_number_calls += 1
            else:
                log.info('No more calls')
        return call is not None


    def get_next_calling_list_entry(self, call):
        return self._calling_list.get_call()


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
        created_calls = self._created_calls.values()

        mystr = ''
        for call in created_calls:
            mystr += '{} '.format( call.unique_id)

        log.debug('')
        log.debug('Report:')
        log.debug('  current_time:                    {}'.format(self.millis_to_hours(self._current_time)))
        log.debug('  number_created_calls:            {} ({})'.format(self.number_created_calls(), mystr))
        log.debug('  number_ringing_calls:            {}'.format(self.number_ringing_calls()))
        log.debug('  number_queued_calls:             {}'.format(self.number_queued_calls()))
        log.debug('  number_talking_calls:            {}'.format(self.number_talking_calls()))
        log.debug('  number_disconnected_calls:       {}'.format(self.number_disconnected_calls()))
        log.debug('  number_free_agents:              {}'.format(self._number_free_agents))
        log.debug('  number_busy_agents:              {}'.format(self._number_busy_agents))
        log.debug('  total_number_answered_calls:     {}'.format(self.total_number_answered_calls))
        log.debug('  total_number_not_answered_calls: {}'.format(self.total_number_not_answered_calls))
        log.debug('  total_number_abandon_calls:      {}'.format(self.total_number_abandon_calls))
        log.debug('  total_number_talking_calls:      {}'.format(self.total_number_talking_calls))
        log.debug('  total_number_calls:              {}'.format(self.total_number_calls))
        log.debug('  total_agent_idle_time:           {}'.format(self.total_agent_idle_time))
        log.debug('  total_agent_talk_time:           {}'.format(self.total_agent_talk_time))


    def print_end_report(self):
        log.info('')
        log.info('Report:')
        log.info('  abandonment rate: {:02.2f}%'.format( self._current_abandonment_rate * 100 ))
        log.info('  talk time:        {:.2f}% ({:.2f} mins)'.format(self._current_talk_time * 100, self._current_talk_time * 60))


    def millis_to_hours(self, millis):
        secs, millis = divmod(millis, 1000)
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)

        return '{:02d}:{:02d}:{:02d}.{}'.format(hours, mins, secs, millis)


    def recalc_dial_level(self):
        """
        This is where the predictive dialer implementations implement their individual algorithms
        to calculate the number of calls to make.
        :return: an integer that represents the number of calls for the dialer to make
        """
        return 0



