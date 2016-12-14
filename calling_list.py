from os import listdir
import pandas as pd
import logging as log

from callstats import CallStats, QueuedStats


class CallingList:

    def __init__(self):
        self._df = {}

        self._calls = []
        self._queued_calls = []
        self._next_queued_call = 0


    def load(self, filename):
        log.info('Loading simulation file: {}'.format(filename))
        self._df = pd.read_csv(filename, infer_datetime_format=True)


    def parse(self):
        log.info('Parsing simulation file.')

        # Reset our storage
        self._calls = []
        self._queued_calls = []
        self._next_queued_call = 0

        for row in self._df.itertuples():

            #log.debug(row)
            c = CallStats(row.CallStartDateTime, row.OutcomeCode, row.OffsetConnect,
                          row.OffsetDisconnect,row.CallEndDateTime, row.UniqueId, row.CauseCode,
                          row.QueuedStartDateTime, row.QueuedEndDateTime, row.Queued, row.TransferredToAgent)

            self._calls.append(c)

            if row.Queued == 1:
                q = QueuedStats(row.CallStartDateTime, row.OutcomeCode, row.OffsetConnect,
                                row.OffsetDisconnect,row.CallEndDateTime, row.UniqueId, row.CauseCode,
                                row.QueuedStartDateTime, row.QueuedEndDateTime, row.Queued, row.TransferredToAgent)

                self._queued_calls.append(q)


    def get_call(self):
        if len(self._calls) > 0:
            return self._calls.pop(0)
        else:
            return None


    def get_number_calls(self):
        return len(self._calls)


    def get_queued_call(self):
        if len(self._queued_calls) == 0:
            return None

        # If we've used up all of our queued calls then start at the beginning
        if self._next_queued_call >= len(self._queued_calls):
            self._next_queued_call = 0

        # Retrieve the next queued call
        queued_call = self._queued_calls[self._next_queued_call]

        # Move along one for the next time
        self._next_queued_call += 1

        return queued_call


