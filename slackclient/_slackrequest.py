import time
import urllib
import urllib2
import requests


class SlackRequest(object):
    def __init__(self):
        pass

    def do(self, token, request="?", post_data={}, domain="slack.com"):
        t = time.time()
        post_data["ts"] = t
        post_data["token"] = token
        post_data = urllib.urlencode(post_data)
        url = 'https://{0}/api/{1}'.format(domain, request)
        res = requests.post(url, data=post_data)
        return urllib2.urlopen(url, post_data)

