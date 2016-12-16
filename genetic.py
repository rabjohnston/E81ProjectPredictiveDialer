
# File: genetic.py
#    from _Genetic Algorithms with Python_, an ebook
#    available for purchase at http://leanpub.com/genetic_algorithms_with_python
#
# Author: Clinton Sheppard <fluentcoder@gmail.com>
# Repository: https://github.com/handcraftsman/genetical
# Copyright (c) 2016 Clinton Sheppard
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

import random
import statistics
import time
import sys
from bisect import bisect_left
from math import exp
from enum import Enum
from enum import IntEnum


def _generate_parent(length, geneSet, get_fitness):
    genes = []
    while len(genes) < length:
        sampleSize = min(length - len(genes), len(geneSet))
        genes.extend(random.sample(geneSet, sampleSize))
    fitness = get_fitness(genes)
    return Chromosome(genes, fitness, Strategies.Create)


def _mutate(parent, geneSet, get_fitness):
    childGenes = parent.Genes[:]
    index = random.randrange(0, len(parent.Genes))
    newGene, alternate = random.sample(geneSet, 2)
    childGenes[index] = alternate \
        if newGene == childGenes[index] \
        else newGene
    fitness = get_fitness(childGenes)
    return Chromosome(childGenes, fitness, Strategies.Mutate)


def _mutate_custom(parent, custom_mutate, get_fitness):
    childGenes = parent.Genes[:]
    custom_mutate(childGenes)
    fitness = get_fitness(childGenes)
    return Chromosome(childGenes, fitness, Strategies.Mutate)


def _crossover(parentGenes, index, parents, get_fitness, crossover, mutate, generate_parent):
    donorIndex = random.randrange(0, len(parents))
    if donorIndex == index:
        donorIndex = (donorIndex + 1) % len(parents)
    childGenes = crossover(parentGenes, parents[donorIndex].Genes)
    if childGenes is None:
        # parent and donor are indistinguishable
        parents[donorIndex] = generate_parent()
        return mutate(parents[index])
    fitness = get_fitness(childGenes)
    return Chromosome(childGenes, fitness, Strategies.Crossover)


def get_best(get_fitness, targetLen, optimalFitness, geneSet,
             display, custom_mutate=None, custom_create=None,
             maxAge=None, poolSize=1, crossover=None,
             maxSeconds=None):
    """
    attempts to find the set of genes with the best fitness.
    :param get_fitness: (func (Cromosome) => object implementing __gt__): should return an value representing how close that particular candidate comes to the optimal solution.  Higher values are better. Object returned must at least implement __gt__
    :param targetLen: (int): length to use when creating gene sequences using the built in generator.
    :param optimalFitness: (object implementing __gt__): expected fitness value for the best solution. Stops execution if found.
    :param geneSet: (list): optional list of gene values for generating new gene sequences.  If not provided, custom_create must be provided.
    :param display: (func (Chromosome)): Called to provide visual output of better candidates as they are discovered.
    :param custom_mutate: (func (list(gene object))): optional replacement for the built in mutate function.  Called with an array of child genes.  Changes should be made to the child genes.
    :param custom_create: (func => list(gene object)): optional function to create a gene sequence.  If not provided, geneSet must be provided.
    :param maxAge: (int): number of rounds before a given genetic line is allowed to die out.
    :param poolSize: (int): number of parents in the pool.  Defaults to 1.
    :param crossover: (func (list(gene object), list(gene object))=> list(gene object)): crossover function. Called with the two parents, should return an array of genes.
    :param maxSeconds: (int): maximum number of seconds to run without improvement.
    :return: a Chromosome object

    Examples:

        import datetime
        from genetical import genetic
        import unittest


        def get_fitness(guess, target):
            return sum(1 for expected, actual in zip(target, guess)
                       if expected == actual)


        def display(candidate, startTime):
            timeDiff = datetime.datetime.now() - startTime
            print("{0}\t{1}\t{2}".format(
                ''.join(candidate.Genes),
                candidate.Fitness,
                str(timeDiff)))


        class GuessPasswordTests(unittest.TestCase):
            geneset = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!.,"

            def test_Hello_World(self):
                target = "Hello World!"
                self.guess_password(target)

            def test_For_I_am_fearfully_and_wonderfully_made(self):
                target = "For I am fearfully and wonderfully made."
                self.guess_password(target)

            def guess_password(self, target):
                startTime = datetime.datetime.now()

                def fnGetFitness(genes):
                    return get_fitness(genes, target)

                def fnDisplay(candidate):
                    display(candidate, startTime)

                optimalFitness = len(target)
                best = genetic.get_best(fnGetFitness, len(target),
                                        optimalFitness, self.geneset, fnDisplay)

                self.assertEqual(''.join(best.Genes), target)

        if __name__ == '__main__':
            unittest.main()
    """
    if custom_mutate is None:
        def fnMutate(parent):
            return _mutate(parent, geneSet, get_fitness)
    else:
        def fnMutate(parent):
            return _mutate_custom(parent, custom_mutate, get_fitness)

    if custom_create is None:
        def fnGenerateParent():
            return _generate_parent(targetLen, geneSet, get_fitness)
    else:
        def fnGenerateParent():
            genes = custom_create()
            return Chromosome(genes, get_fitness(genes), Strategies.Create)

    strategyLookup = {
        Strategies.Create: lambda p, i, o: fnGenerateParent(),
        Strategies.Mutate: lambda p, i, o: fnMutate(p),
        Strategies.Crossover: lambda p, i, o: _crossover(p.Genes, i, o, get_fitness, crossover, fnMutate,
                                                         fnGenerateParent)
    }

    usedStrategies = [strategyLookup[Strategies.Mutate]]
    if crossover is not None:
        usedStrategies.append(strategyLookup[Strategies.Crossover])

        def fnNewChild(parent, index, parents):
            return random.choice(usedStrategies)(parent, index, parents)
    else:
        def fnNewChild(parent, index, parents):
            return fnMutate(parent)

    for timedOut, improvement in _get_improvement(fnNewChild, fnGenerateParent, maxAge, poolSize, maxSeconds):
        if timedOut:
            return improvement
        display(improvement)
        f = strategyLookup[improvement.Strategy]
        usedStrategies.append(f)
        if not optimalFitness > improvement.Fitness:
            return improvement


def _get_improvement(new_child, generate_parent, maxAge, poolSize, maxSeconds):
    startTime = time.time()
    bestParent = generate_parent()
    yield maxSeconds is not None and time.time() - startTime > maxSeconds, bestParent
    parents = [bestParent]
    historicalFitnesses = [bestParent.Fitness]
    for _ in range(poolSize - 1):
        parent = generate_parent()
        if maxSeconds is not None and time.time() - startTime > maxSeconds:
            yield True, parent
        if parent.Fitness > bestParent.Fitness:
            yield False, parent
            bestParent = parent
            historicalFitnesses.append(parent.Fitness)
        parents.append(parent)
    lastParentIndex = poolSize - 1
    pindex = 1
    while True:
        if maxSeconds is not None and time.time() - startTime > maxSeconds:
            yield True, bestParent
        pindex = pindex - 1 if pindex > 0 else lastParentIndex
        parent = parents[pindex]
        child = new_child(parent, pindex, parents)
        if parent.Fitness > child.Fitness:
            if maxAge is None:
                continue
            parent.Age += 1
            if maxAge > parent.Age:
                continue
            index = bisect_left(historicalFitnesses, child.Fitness, 0, len(historicalFitnesses))
            difference = len(historicalFitnesses) - index
            proportionSimilar = difference / len(historicalFitnesses)
            if random.random() < exp(-proportionSimilar):
                parents[pindex] = child
                continue
            parents[pindex] = bestParent
            parent.Age = 0
            continue
        if not child.Fitness > parent.Fitness:
            # same fitness
            child.Age = parent.Age + 1
            parents[pindex] = child
            continue
        parents[pindex] = child
        parent.Age = 0
        if child.Fitness > bestParent.Fitness:
            yield False, child
            bestParent = child
            historicalFitnesses.append(child.Fitness)


def hill_climbing(optimizationFunction, is_improvement, is_optimal,
                  get_next_feature_value, display, initialFeatureValue):
    best = optimizationFunction(initialFeatureValue)
    stdout = sys.stdout
    sys.stdout = None
    while not is_optimal(best):
        featureValue = get_next_feature_value(best)
        child = optimizationFunction(featureValue)
        if is_improvement(best, child):
            best = child
            sys.stdout = stdout
            display(best, featureValue)
            sys.stdout = None
    sys.stdout = stdout
    return best


def tournament(generate_parent, crossover, compete, display, sort_key, numParents=10, max_generations=100):
    pool = [[generate_parent(), [0, 0, 0]] for _ in range(1 + numParents * numParents)]
    best, bestScore = pool[0]

    def getSortKey(x):
        return sort_key(x[0], x[1][CompetitionResult.Win], x[1][CompetitionResult.Tie], x[1][CompetitionResult.Loss])

    generation = 0
    while generation < max_generations:
        generation += 1
        for i in range(0, len(pool)):
            for j in range(0, len(pool)):
                if i == j:
                    continue
                playera, scorea = pool[i]
                playerb, scoreb = pool[j]
                result = compete(playera, playerb)
                scorea[result] += 1
                scoreb[2 - result] += 1

        pool.sort(key=getSortKey, reverse=True)
        if getSortKey(pool[0]) > getSortKey([best, bestScore]):
            best, bestScore = pool[0]
            display(best, bestScore[CompetitionResult.Win],
                    bestScore[CompetitionResult.Tie],
                    bestScore[CompetitionResult.Loss], generation)

        parents = [pool[i][0] for i in range(numParents)]
        pool = [[crossover(parents[i], parents[j]), [0, 0, 0]]
                for i in range(len(parents))
                for j in range(len(parents))
                if i != j]
        pool.extend([parent, [0, 0, 0]] for parent in parents)
        pool.append([generate_parent(), [0, 0, 0]])
    return best


class CompetitionResult(IntEnum):
    Loss = 0,
    Tie = 1,
    Win = 2,


class Chromosome:
    Genes = None
    Fitness = None
    Age = 0
    Strategy = None

    def __init__(self, genes, fitness, strategy):
        self.Genes = genes
        self.Fitness = fitness
        self.Strategy = strategy


class Strategies(Enum):
    Create = 0,
    Mutate = 1,
    Crossover = 2


class Benchmark:
    @staticmethod
    def run(function):
        timings = []
        stdout = sys.stdout
        for i in range(100):
            sys.stdout = None
            startTime = time.time()
            function()
            seconds = time.time() - startTime
            sys.stdout = stdout
            timings.append(seconds)
            mean = statistics.mean(timings)
            if i < 10 or i % 10 == 9:
                print("{0} {1:3.2f} {2:3.2f}".format(
                    1 + i, mean,
                    statistics.stdev(timings, mean)
                    if i > 1 else 0))
