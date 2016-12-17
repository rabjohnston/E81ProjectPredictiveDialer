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
    DEBUG and above is logged to file.
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

    ##while cl.get_number_calls() > 0:
    ##cc = SimulationConstantCall(0.5)
    #cc = SimulationFreeAgent()
    cc = SimulationGenetic()
    #cc = SimulationAnalytic()
    cc.start(cl)


if __name__ == '__main__':
    main()
