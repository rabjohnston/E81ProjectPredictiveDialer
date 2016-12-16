from simulation_constant_call import SimulationConstantCall
from simulation import Simulation
from calling_list import CallingList
import genetic
import datetime
import random
import math
import logging as log


class SimulationGenetic(SimulationConstantCall):

    def __init__(self):
        SimulationConstantCall.__init__(self)

        self._stored_calling_list_entry = []

        self._last_stored_calling_list_entry = 0

        self.RECALC_INTERVAL = Simulation.ONE_MINUTE * 30
        self.RECALC_WINDOW = Simulation.ONE_MINUTE * 10

        # When initialising the chromosones we need a window to define the upper and lower limit
        # of of values that the random generator can take on.
        self._CHROMOSONE_INIT_WINDOW = 2


    def get_next_calling_list_entry(self, call):
        call = self._calling_list.get_call()

        if call is not None:
            # Save this calling list entry for later use by genetic algorithm
            self._stored_calling_list_entry.append(call)

        return call


    def calculate_calls(self):
        """
        Based on the dial level, calculate how many calls we need to generate
        """
        number_calls_to_make = 0

        # Determine whether we need to recalculate the dial level. As we are taking a slice of the past calls
        # (determined by RECALC_WINDOW) we need to ensure that enough time has elapsed at the beginning of the campaign
        # to ensure we have enough data to run the first calculation.
        if (self._current_time % self.RECALC_INTERVAL == 0) and self._current_time >= self.RECALC_WINDOW \
                and not self.dialer_stopping():
            self.rerun_past_calls()

        return SimulationConstantCall.calculate_calls(self)


    def rerun_past_calls(self):
        current_dial_level = self._dial_level
        cl = CallingList(self._stored_calling_list_entry[self._last_stored_calling_list_entry:], self._calling_list._queued_calls)
        self._last_stored_calling_list_entry = len(self._stored_calling_list_entry)

        # We've used up 'n-1' calling entries - clear it in preparation of 'n' calling list entries
        #self._stored_calling_list_entry = []

        log.info('')
        log.info('Running Generic Algorithm Simulation')
        log.info('')



        def fnCreate():
            # Define the range that the dial level can take
            upper = current_dial_level + self._CHROMOSONE_INIT_WINDOW
            lower = math.min(current_dial_level - self._CHROMOSONE_INIT_WINDOW)
            random.triangular(current_dial_level, )
            return random.sample(geneset, len(geneset))

        def fnDisplay(candidate):
            display(candidate, startTime)

        def fnGetFitness(genes):
            return get_fitness(genes)

        def fnMutate(genes):
            mutate(genes, fnGetFitness)

        def fnCrossover(parent, donor):
            return crossover(parent, donor, fnGetFitness)

        optimalFitness = fnGetFitness(optimalSequence)

        startTime = datetime.datetime.now()
        best = genetic.get_best(fnGetFitness, None, optimalFitness, None,
                                fnDisplay, fnMutate, fnCreate, maxAge=500,
                                poolSize=25, crossover=fnCrossover)


        scc = SimulationConstantCall(current_dial_level, stop_immediately_when_no_calls=True) #, name='Generic({:02.2f})'.format(self._current_time))
        scc.start(cl)

        self._dial_level = scc._dial_level




    def get_fitness(genes, idToLocationLookup):
        fitness = get_distance(idToLocationLookup[genes[0]],
                               idToLocationLookup[genes[-1]])

        for i in range(len(genes) - 1):
            start = idToLocationLookup[genes[i]]
            end = idToLocationLookup[genes[i + 1]]
            fitness += get_distance(start, end)

        return Fitness(round(fitness, 2))