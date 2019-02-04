#!/usr/bin/python3
from __future__ import print_function

from html.parser import HTMLParser
import json
import logging
import os
import re
import requests
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('requests').setLevel(logging.ERROR)

session = requests.Session()

username = os.environ['COMCAST_USERNAME']
password = os.environ['COMCAST_PASSWORD']

logger.debug("Finding form inputs for login...")
res = session.get('https://customer.xfinity.com/oauth/force_connect/?continue=%23%2Fdevices')
#res = session.get('https://login.comcast.net/login?r=comcast.net&s=oauth&continue=https%3A%2F%2Flogin.comcast.net%2Foauth%2Fauthorize%3Fclient_id%3Dmy-account-web%26redirect_uri%3Dhttps%253A%252F%252Fcustomer.xfinity.com%252Foauth%252Fcallback%26response_type%3Dcode%26state%3D%2523%252Fdevices%26response%3D1&client_id=my-account-web')
assert res.status_code == 200
data = {x[0]: HTMLParser().unescape(x[1]) for x in re.finditer(r'<input.*?name="(.*?)".*?value="(.*?)".*?>', res.text)}
logger.debug("Found with the following input fields: {}".format(data))
data = {
    'user': username,
    'passwd': password,
    **data
}

logger.debug("Posting to login...")
res = session.post('https://login.xfinity.com/login', data=data)
assert res.status_code == 200

logger.debug("Fetching internet usage AJAX...")
res = session.get('https://customer.xfinity.com/apis/services/internet/usage')
#logger.debug("Resp: %r", res.text)
assert res.status_code == 200

js = json.loads(res.text)

out = {
    'raw': js,
    'used': js['usageMonths'][-1]['homeUsage'],
    'total': js['usageMonths'][-1]['allowableUsage'],
    'unit': js['usageMonths'][-1]['unitOfMeasure'],
}
print(json.dumps(out))
