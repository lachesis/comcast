#!/usr/bin/python3
from __future__ import print_function

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

logger.debug("Finding req_id for login...")
res = session.get('https://customer.xfinity.com/oauth/force_connect/?continue=%23%2Fdevices')
#res = session.get('https://login.comcast.net/login?r=comcast.net&s=oauth&continue=https%3A%2F%2Flogin.comcast.net%2Foauth%2Fauthorize%3Fclient_id%3Dmy-account-web%26redirect_uri%3Dhttps%253A%252F%252Fcustomer.xfinity.com%252Foauth%252Fcallback%26response_type%3Dcode%26state%3D%2523%252Fdevices%26response%3D1&client_id=my-account-web')
assert res.status_code == 200
m = re.search(r'<input type="hidden" name="reqId" value="(.*?)">', res.text)
req_id = m.group(1)
logger.debug("Found req_id = %r", req_id)

data = {
    'user': username,
    'passwd': password,
    'reqId': req_id,
    'deviceAuthn': 'false',
    's': 'oauth',
    'forceAuthn': '1',
    'r': 'comcast.net',
    'ipAddrAuthn': 'false',
    'continue': 'https://oauth.xfinity.com/oauth/authorize?client_id=my-account-web&prompt=login&redirect_uri=https%3A%2F%2Fcustomer.xfinity.com%2Foauth%2Fcallback&response_type=code&state=%23%2Fdevices&response=1',
    'passive': 'false',
    'client_id': 'my-account-web',
    'lang': 'en',
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
