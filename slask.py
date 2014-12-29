#!/usr/bin/env python

from __future__ import print_function
from config import config
from glob import glob
import importlib
import os
import re
from slackclient import SlackClient
import sys
import time
import traceback
import logging


class Slask(object):

    LOG_FORMAT = '%(asctime)-15s [%(levelname)s] %(filename)s (line: %(lineno)d): %(message)s'

    def __init__(self, daemonize=False, verbose=False):
        if daemonize:
            self.stdin_path = '/dev/null'
            self.stdout_path = '/tmp/slask.out'
            self.stderr_path = '/tmp/slask.err'
            self.pidfile_path = '/tmp/slask.pid'
            self.pidfile_timeout = 1
            self.log_path = '/tmp/slask.log'
            logging.basicConfig(format=self.LOG_FORMAT)
        else:
            logging.basicConfig(format=self.LOG_FORMAT)
        self.log = logging.getLogger("SLASK")
        if verbose:
            self.log.setLevel(logging.DEBUG)
        self.hooks = dict()
        self.event_handlers = None

    def run(self):
        self.log.info("Event Processor Started")
        self.init_plugins()
        self._connect_to_slack()
        self.event_handlers = {
            "message": self.handle_message
        }
        while True:
            self._process_events(self._get_events())
            time.sleep(1)

    def _connect_to_slack(self):
        self.log.info("Connecting to Slack")
        self.slack_client = SlackClient(config["token"])
        self.slack_client.rtm_connect()

    def _get_events(self):
        self.log.debug("Fetching new events")
        return self.slack_client.rtm_read()

    def _process_events(self, events):
        self.log.debug("Processing {0} events".format(len(events)))
        event_num = 1
        for event in events:
            self.log.debug("Processing event {0} of {1}".format(event_num, len(events)))
            self.log.debug("Found event of type {0}".format(event.get("type")))
            self.log.debug(event.keys())
            handler = self.event_handlers.get(event.get("type"))
            if handler:
                self.log.debug("Event handler found, processing event")
                event_process_stime = time.time()
                handler(self.slack_client, event)
                self.log.debug("Event processed in {0:.2f} seconds".format(time.time() - event_process_stime))
            event_num += 1

    def init_plugins(self):
        self.log.info("Locating plugins")
        os.chdir(config.get("install_path"))
        plugins = glob("plugins/[!_]*.py")
        self.log.info("Found {0} potential plugins".format(len(plugins)))
        plugin_num = 1
        bad_plugins = 0
        for plugin in plugins:
            self.log.info("Processing plugin {0} of {1}".format(plugin_num, len(plugins)))
            self.log.debug("Initializing {0}".format(plugin))
            try:
                mod = importlib.import_module(plugin.replace(os.path.sep, ".")[:-3])
                modname = mod.__name__.split('.')[1]
                for hook in re.findall("on_(\w+)", " ".join(dir(mod))):
                    hookfun = getattr(mod, "on_" + hook)
                    self.log.debug("Attaching {0}.{1} to {2}".format(modname, hookfun, hook))
                    self.hooks.setdefault(hook, []).append(hookfun)

                if mod.__doc__:
                    firstline = mod.__doc__.split('\n')[0]
                    self.hooks.setdefault('help', {})[modname] = firstline
                    self.hooks.setdefault('extendedhelp', {})[modname] = mod.__doc__

            # Except everything to handle bad plugin imports
            # We don't want to die because the plugin is bad
            except:
                bad_plugins += 1
                self.log.error("Plugin import failed on module {0}, module not loaded".format(plugin))
                self.log.error("{0}".format(sys.exc_info()[0]))
                self.log.error("{0}".format(traceback.format_exc()))
            plugin_num += 1
        self.log.info("{0} of {1} plugins processed successfully".format(len(plugins) - bad_plugins, len(plugins)))

    def run_hook(self, hook, data, server):
        responses = []
        for h in self.hooks.get(hook, []):
            h_response = h(data, server)
            if h_response:
                responses.append(h_response)
        return responses

    def handle_message(self, client, event):
        # ignore bot messages and edits
        subtype = event.get("subtype", "")
        if subtype == "bot_message" or subtype == "message_changed":
            return

        botname = self.slack_client.server.login_data["self"]["name"]
        try:
            msguser = client.server.users.get(event["user"])
        except KeyError:
            print("event {0} has no user".format(event))
            return

        if msguser["name"] == botname or msguser["name"].lower() == "slackbot":
            return

        text = "\n".join(self.run_hook("message", event, {"client": client, "config": config, "hooks": self.hooks}))

        if text:
            self.log.debug("Sending message to Slack")
            self.log.debug("MSG: {0}".format(text))
            client.rtm_send_message(event["channel"], text)
        else:
            self.log.debug("No message content to send to Slack")


if __name__ == "__main__":
    print("And away we go...")
    s = Slask(daemonize=False, verbose=True)
    s.run()