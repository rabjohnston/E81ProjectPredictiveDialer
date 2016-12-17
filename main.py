from simulation_constant_call import SimulationConstantCall
from simulation_free_agent import SimulationFreeAgent
from simulation_genetic import SimulationGenetic
from simulation_analytic import SimulationAnalytic

from calling_list import CallingList
import logging as log
import random
import sys


def setup_logging():
    """
    Setup the logging. INFO and above are logged to console.
    DEBUG and above is logged to file (this can stretch to hundreds of Mb if running the genetic algorithm)
    :return:
    """
    log.basicConfig(level=log.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='logfile.log',
                    filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = log.StreamHandler()
    console.setLevel(log.INFO)
    # set a format which is simpler for console use
    formatter = log.Formatter('%(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    log.getLogger('').addHandler(console)


def main():
    """
    Simple wrapper to run a simulation using different algorithms.

    Requires small.csv file - too big for Canvas. Can be found on github repo :

      https://github.com/rabjohnston/E81ProjectPredictiveDialer

    :return:
    """

    setup_logging()

    log.info('------------------------------------------------------------------------------------------------------')
    log.info('Start')
    log.info('------------------------------------------------------------------------------------------------------')

    # Make sure we can reproduce our results
    random.seed(42)

    # Create one calling list
    cl = CallingList()
    cl.load('small.csv')
    cl.parse()

    # The constant rate dialer. Changing the parameter will change the dial level. This algorithm will complete
    # fairly quickly.
    ##cc = SimulationConstantCall(0.5)

    # The progressive dialer (aka free agent). This algorithm waits until an agent is free and then generates
    # a call for them. Similar to the constant call algorithm, this one is also quick.
    #cc = SimulationFreeAgent()

    # The generic algorithm. This one will take a long time to run and outputs a large debug logfile (hundreds of Mb)
    # You might want to comment out the logging to file.
    cc = SimulationGenetic()

    # The analytic algorithm. There are problems with this and I would question whether it will even work using real
    # data rather than synthetic data.

    #cc = SimulationAnalytic()
    cc.start(cl)


if __name__ == '__main__':
    main()
