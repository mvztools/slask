#!/usr/bin/env python

from daemon import runner
from daemon.runner import DaemonRunnerStopFailureError
import sys
import os.path


from slask import Slask

if __name__ == "__main__":
    if sys.argv[1] == "start":
        print("Initializing Daemon...")
    elif sys.argv[1] == "stop":
        print("Stopping Daemon...")
    elif sys.argv[1] == "restart":
        print("Restarting Daemon...")

    s = Slask(daemonize=True)
    try:
        daemon_runner = runner.DaemonRunner(s)
        daemon_runner.do_action()
    except DaemonRunnerStopFailureError as e:
        if not os.path.exists(s.pidfile_path):
            print("ERROR: PID File does not exist, cannot stop anything")
        else:
            raise e