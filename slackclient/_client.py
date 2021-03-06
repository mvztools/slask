#!/usr/bin/python
#mostly a proxy object to abstract how some of this works

import json
import logging
from _server import Server


class SlackNotConnected(Exception):
    pass


class SlackClient(object):

    def __init__(self, token):
        self.log = logging.getLogger("SLASK")
        self.token = token
        self.server = Server(self.token, False)

    def rtm_connect(self):
        try:
            self.server.rtm_connect()
            self.log.info("Connected to Slack successfully")
            return True
        except:
            self.log.error("Connection to Slack failed")
            return False

    def api_call(self, method, **kwargs):
        return self.server.api_call(method, kwargs)

    def rtm_read(self):
        #in the future, this should handle some events internally i.e. channel creation
        if self.server:
            json_data = self.server.websocket_safe_read()
            data = []
            if json_data != '':
                for d in json_data.split('\n'):
                    data.append(json.loads(d))
            return data
        else:
            raise SlackNotConnected

    def rtm_send_message(self, channel, message):
        return self.server.channels.find(channel).send_message(message)
