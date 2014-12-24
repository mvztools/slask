import time
import requests


class SlackRequest(object):
    def __init__(self):
        pass

    def do(self, token, request="?", post_data={}, domain="slack.com"):
        t = time.time()
        post_data["ts"] = t
        post_data["token"] = token
        url = 'https://{0}/api/{1}'.format(domain, request)
        return requests.post(url, data=post_data)

