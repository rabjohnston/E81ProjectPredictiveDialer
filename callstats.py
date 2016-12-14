from enum import Enum
from collections import OrderedDict
from datetime import datetime
import logging as log

CallState = Enum('CallState', ['created', 'ringing', 'answered', 'queued', 'talking', 'disconnected'])


class CallEvent:
    def __init__(self, time, state):
        self.time = time
        self.state = state


class QueuedStats:
    """
    CallStartDateTime, OutcomeCode, OffsetConnect, OffsetAgentRoute, OffsetDisconnect,
                 CallEndDateTime, UniqueId, CauseCode, QueuedStartDateTime, QueuedEndDateTime, Queued,
                 TransferredToAgent
    """

    def __init__(self, callStartDateTime, outcome_code, offsetConnect, offsetDisconnect,
                 callEndDateTime, uniqueId, causeCode, queuedStartDateTime, queuedEndDateTime, queued,
                 transferredToAgent):

        DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
        TIME_TO_CREATE_CALL = 3000 # 3s to create a call

        self._callStartDateTime = datetime.strptime(callStartDateTime, DATE_FORMAT)
        self._callEndDateTime = datetime.strptime(callEndDateTime, DATE_FORMAT)
        self.outcome_code = outcome_code
        self._offsetConnect = offsetConnect

        # We don't always get a disconnect offset - we can calculate one however..
        if offsetDisconnect == 0:
            self._offsetDisconnect = (self._callEndDateTime - self._callStartDateTime).microseconds / 1000
        else:
            self._offsetDisconnect = offsetDisconnect

        self.unique_id = uniqueId
        self._causeCode = causeCode

        if( type(queuedStartDateTime) == str):
            self._queuedStartDateTime = datetime.strptime(queuedStartDateTime, DATE_FORMAT)

        if (type(queuedEndDateTime) == str):
            self._queuedEndDateTime = datetime.strptime(queuedEndDateTime, DATE_FORMAT)

        self._queued = queued == 1
        self._transferredToAgent = transferredToAgent == 1

        # The time it takes to generate a call.
        self._offset_call_creation = TIME_TO_CREATE_CALL

        # A list of all the events that will happen to this call
        self._future_events = []
        self._call_state = None


class CallStats:
    """
    CallStartDateTime, OutcomeCode, OffsetConnect, OffsetAgentRoute, OffsetDisconnect,
                 CallEndDateTime, UniqueId, CauseCode, QueuedStartDateTime, QueuedEndDateTime, Queued,
                 TransferredToAgent
    """

    def __init__(self, callStartDateTime, outcomeCode, offsetConnect, offsetDisconnect,
                 callEndDateTime, uniqueId, causeCode, queuedStartDateTime, queuedEndDateTime, queued,
                 transferredToAgent):

        DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
        TIME_TO_CREATE_CALL = 3000 # 3s to create a call

        self._callStartDateTime = datetime.strptime(callStartDateTime, DATE_FORMAT)
        self.outcome_code = outcomeCode
        self._offsetConnect = offsetConnect
        self._callEndDateTime = datetime.strptime(callEndDateTime, DATE_FORMAT)
        self.unique_id = uniqueId
        self._causeCode = causeCode

        # We don't always get a disconnect offset - we can calculate one however..
        if offsetDisconnect == 0:
            self._offsetDisconnect = (self._callEndDateTime - self._callStartDateTime).total_seconds() * 1000
        else:
            self._offsetDisconnect = offsetDisconnect

        if type(queuedStartDateTime) == str:
            self._queuedStartDateTime = datetime.strptime(queuedStartDateTime, DATE_FORMAT)

        if type(queuedEndDateTime) == str:
            self._queuedEndDateTime = datetime.strptime(queuedEndDateTime, DATE_FORMAT)

        self._queued = queued == 1
        self._transferredToAgent = transferredToAgent == 1

        # The time it takes to generate a call.
        self._offset_call_creation = TIME_TO_CREATE_CALL

        # A list of all the events that will happen to this call
        self._future_events = []
        self._call_state = None

        self._birth_time = None


    def dial(self, birth_time ):
        self._birth_time = birth_time

        self._call_state = CallState.created

        self.calculate_future_events()


    def talking(self, current_time):
        """
        This call got answered and we're talking to an agent. Next thing is to stop talking...
        :param current_time:
        :return:
        """
        self._future_events.append(CallEvent(current_time + self._offsetDisconnect, CallState.disconnected))


    def queued(self, current_time, queued_call):
        """
        This call has been queued. We calculate the disconnect time for the remote end to discinnect from the queue
         if it doesn't get answered by an agent.
        :param current_time:
        :param queued_call:
        :return:
        """
        self._future_events.append(CallEvent(current_time + queued_call._offsetDisconnect, CallState.disconnected))


    def calculate_future_events(self):
        """
        Calculate all the state transitions and the time in which they will occur.
        :return: Nothing
        """
        # Handle the situation where the call doesn't get answered
        if self.outcome_code in ['O', 'E', 'AM', 'NU', 'CF']:
            self._future_events.append(CallEvent(self._birth_time + self._offset_call_creation, CallState.ringing))
            self._future_events.append(CallEvent(self._birth_time + self._offsetDisconnect, CallState.disconnected))

        # Handle the situation where the call is answered
        elif self.outcome_code in ['TR', 'QD', 'QT', 'AC']:
            self._future_events.append(CallEvent(self._birth_time + self._offset_call_creation, CallState.ringing))
            self._future_events.append(CallEvent(self._birth_time + self._offsetDisconnect, CallState.answered))

        else:
            log.error('Unknown outcome: {}'.format(self.outcome_code))


    def next_event(self, current_time):
        """
        Respond to a tick. If we've got an event that has occurred then remove it from our
        list of future events and return it to the caller.
        :param current_time: the current time in the system
        :return: the event, if we have one, otherwise None.
        """
        if len(self._future_events) == 0:
            return None

        if self._future_events[0].time < current_time:
            ev = self._future_events.pop(0)
            return ev
        else:
            return None
