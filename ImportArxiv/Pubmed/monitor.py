#
# Monitoring thread module
# 
# 2012 by Heinrich Hartmann
# Copyright: CreativeCommons-Share alike
# This work is part of related-work.net
#
"""
This module provides a class MonitorThread that prints
statusinformation about the running program in regular 
intervals to logging.info.
"""

import logging
import threading
from time import time, sleep
from copy import deepcopy

class MonitorThread(threading.Thread):
    """
    This class prints information about a STATUS dictionary
    in regular intervals form another thread into loggin.info.

    Example use:
    >>> STATUS  = {} # dictionary to monitor
    >>> Monitor = MonitorThread(STATUS, interval = 1)

    Start monitoring:
    >>> Monitor.start() 

    Do stuff with here, that modifies STATUS
    
    Stop monitoring:
    >>> Monitor.end()
    """

    def __init__(self,STATUS, interval=2):
        self.STATUS = STATUS
        self.interval = interval
        threading.Thread.__init__(self)

    daemon = True
    terminate  = False

    def run(self):
        sleep(.001)
        start = time()
        LAST_STATUS = deepcopy(self.STATUS)
        while True:
            logging.info('Status: (uptime {0:.1f} sec.)'.format(time() - start) )
            for k,v in self.STATUS.items():
                if type(v) in [int, float]:
                    rate = ((v - LAST_STATUS[k])/float(self.interval) if k in LAST_STATUS else 0)
                    logging.info("* {k:15}: {v:>8}, (rate: {rate:+.1f}/sec)".format(**locals()))
                if type(v) is str:
                    logging.info("* {k:15}: {v:>8}".format(**locals()))

            LAST_STATUS = deepcopy(self.STATUS)

            if self.terminate == True:
                break
            sleep(self.interval)

    def end(self):
        logging.info('{0:=^60}'.format(' SUMMARY '))
        self.terminate = True
        self.join()
