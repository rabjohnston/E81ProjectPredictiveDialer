from simulation_constant_call import SimulationConstantCall
from simulation_free_agent import SimulationFreeAgent
from simulation_genetic import SimulationGenetic
from simulation_analytic import SimulationAnalytic

from calling_list import CallingList
import logging as log
import sys


# def setup_logging():
#     log_formatter = log.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")
#     root_logger = log.getLogger()
#
#     file_handler = log.FileHandler("logfile.log", mode='w+')
#     file_handler.setFormatter(log_formatter)
#     file_handler.setLevel(log.DEBUG)
#     root_logger.addHandler(file_handler)
#
#     console_handler = log.StreamHandler(sys.stdout)
#     console_handler.setFormatter(log_formatter)
#     root_logger.addHandler(console_handler)


def setup_logging2():
    # set up logging to file - see previous section for more details
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
    # log.basicConfig(level=log.DEBUG, filename="logfile", filemode="w+",
    #                    format="%(asctime)-15s %(levelname)-8s %(message)s")

    setup_logging2()

    log.info('------------------------------------------------------------------------------------------------------')
    log.info('Start')
    log.info('------------------------------------------------------------------------------------------------------')

    # Create one calling list
    cl = CallingList()
    cl.load('small.csv')
    cl.parse()

    ##while cl.get_number_calls() > 0:
    #cc = SimulationConstantCall(1)
    # cc = SimulationFreeAgent()
    #cc = SimulationGenetic()
    cc = SimulationAnalytic()
    cc.start(cl)


if __name__ == '__main__':
    main()
