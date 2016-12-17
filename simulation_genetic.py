from simulation_constant_call import SimulationConstantCall
from simulation import Simulation
from calling_list import CallingList
from collections import OrderedDict
import genetic
import datetime
import random
import math
import logging as log


class SimulationGenetic(SimulationConstantCall):

    class Chromosome:
        def __init__(self, dial_level, max_abandonment_rate):
            self.dial_level = dial_level
            self.abandonment_rate = 0
            self.talk_time = 0
            self.max_abandonment_rate = max_abandonment_rate

        def __gt__(self, other):
            return self.fitness() > other.fitness()

        def fitness(self):

            fitness = self.talk_time
            #
            # # How much have we gone over the max abandonment rate
            over_abandoned = self.abandonment_rate - self.max_abandonment_rate
            # if over_abandoned > 0:
            #     # We gone over. Penalise a little for just going over but get serious the higher it goes, e.g.
            #     # 1 percent point over will be penalised by 10%, 2 percent points over will be penalised by 40%
            #     penalty = ((over_abandoned * over_abandoned)*1000) * self.talk_time
            #     fitness += penalty

            if over_abandoned > 0:
                fitness = -over_abandoned

            return fitness

    def __init__(self, number_agents=40):
        SimulationConstantCall.__init__(self, number_agents=40)



        self._last_stored_calling_list_entry = 0

        self.RECALC_INTERVAL = Simulation.ONE_MINUTE * 30
        self.RECALC_WINDOW = Simulation.ONE_MINUTE * 10

        self.population_size = 11

        # Split the population in two (and account for the fct that the current dial level is also to be inserted
        # into the population
        self.population_split, remainder = divmod(self.population_size, 2)

        if remainder != 1:
            raise ValueError('Size of population must be odd.')

        # Number of generations to run the genetic algorithm
        self.number_generations = 20

        # The chance that a child chromosome will mutate
        self._mutate_probability = 0.1


    # def get_next_calling_list_entry(self, call):
    #     call = self._calling_list.get_call()
    #
    #     if call is not None:
    #         # Save this calling list entry for later use by genetic algorithm
    #         self._stored_calling_list_entry.append(call)
    #
    #     return call


    def recalc_dial_level(self):
        """
        Based on the dial level, calculate how many calls we need to generate
        """
        number_calls_to_make = 0

        # Determine whether we need to recalculate the dial level. As we are taking a slice of the past calls
        # (determined by RECALC_WINDOW) we need to ensure that enough time has elapsed at the beginning of the campaign
        # to ensure we have enough data to run the first calculation.
        if (self._current_time % self.RECALC_INTERVAL == 0) and self._current_time >= self.RECALC_WINDOW \
                and not self.dialer_stopping():
            self._dial_level = self.rerun_past_calls()

        return self._dial_level


    def rerun_past_calls(self):

        log.info('')
        log.info('Running Generic Algorithm Simulation')
        log.info('')

        population = self.get_initial_population(self._dial_level, self.population_size)

        for i in range(self.number_generations):
            population = self.evolve(population)

        population.sort(reverse=True)

        self._last_stored_calling_list_entry = len(self._stored_calling_list_entry)

        log.info('')
        log.info('Completed Generic Algorithm Simulation. Best dial level is {}, talk time {:.2f}%'.format(population[0].dial_level, population[0].talk_time))
        log.info('')

        return population[0].dial_level


    def evolve(self, population):
        for c in population:
            cl = CallingList(list(self._stored_calling_list_entry[self._last_stored_calling_list_entry:]),
                             list(self._calling_list._queued_calls))
            c.talk_time, c.abandonment_rate = self.run_simulation(c.dial_level, cl)

        population.sort(reverse=True)

        log.info('Run simulation over population')
        self.display_population(population)

        # Choose best parents
        parents = population[:self.population_split+1]

        population = self.regenerate_population(parents)

        log.info('Regenerated population:')
        self.display_population(population)

        return population




    def regenerate_population(self, parents):

        population = parents
        number_parents = len(parents)
        while len(population) < self.population_size:
            parent1 = random.randint(0, number_parents-1)
            parent2 = random.randint(0, number_parents-1)
            if parent1 != parent2:
                child1, child2 = self.crossover(parents[parent1], parents[parent2])
                population.append(child1)
                population.append(child2)

        return population


    def display_population(self, population):
        log.info('Parents:')

        for p in population:
            log.info('  Talk Time: {}, Dial Level: {}, Abandonment Rate: {}'.format(p.talk_time, p.dial_level, p.abandonment_rate))


    def crossover(self, parent1, parent2):
        weight = random.random()
        child1_dl = (weight * parent1.dial_level) + ((1 - weight) * parent2.dial_level)
        child2_dl = (weight * parent2.dial_level) + ((1 - weight) * parent1.dial_level)

        child1 = self.mutate(SimulationGenetic.Chromosome(child1_dl, self.max_abandonment_rate))
        child2 = self.mutate(SimulationGenetic.Chromosome(child2_dl, self.max_abandonment_rate))

        return child1, child2


    def mutate(self, chromosome):
        if self._mutate_probability > random.random():
            dl = chromosome.dial_level
            chromosome.dial_level = random.triangular(dl * 0.5, dl * 1.5)
            log.debug('Mutated from {} to {}'.format(dl, chromosome.dial_level))

        return chromosome


    def get_initial_population(self, dial_level, population_size):
        """
        Generate five below and five above.
        :param dial_level:
        :param population_size:
        :return: an array of chromosomes
        """

        population = []

        for i in range(self.population_split):
            chromosome = random.triangular(0, dial_level - 0.01)
            population.append(SimulationGenetic.Chromosome(chromosome, self.max_abandonment_rate))

        population.append(SimulationGenetic.Chromosome(dial_level, self.max_abandonment_rate))

        for i in range(self.population_split):
            chromosome = random.triangular( dial_level + 0.01, self.max_dial_level)
            population.append(SimulationGenetic.Chromosome(chromosome, self.max_abandonment_rate))

        return population


    def run_simulation(self, dial_level, cl):
        scc = SimulationConstantCall(dial_level, stop_immediately_when_no_calls=True, generate_history_file=False)
        scc.start(cl)

        return scc._current_talk_time, scc._current_abandonment_rate










