import datetime
import html
import logging
import os
import re
import sys
import time
import requests

def main():
    logging.basicConfig(level=logging.DEBUG)
    sess = requests.Session()

    username = os.getenv('PGE_USERNAME')
    password = os.getenv('PGE_PASSWORD')

    if not username or not password:
        raise ValueError("Supply PGE_USERNAME and PGE_PASSWORD env vars")

    # log in to PGE
    url = "https://apim.pge.com/login"
    doc = {"username":username,"password":password,"globalsync":True,"type":"LOGIN"}
    head = {'Origin': 'https://www.pge.com', 'Referer': 'https://www.pge.com/', 'User-Agent': 'Mozilla/5.0'}
    qs = {'ts': int(time.time())}
    resp = sess.post(url, json=doc, params=qs, headers=head, timeout=31)
    resp.raise_for_status()

    # start SAML auth (Origin pge.com)
    url = "https://www.pge.com/affwebservices/public/saml2sso"
    qs = {'RelayState': 'https://pge.opower.com/ei/app/r/energy-usage-details', 'SPID': 'sso.opower.com'}
    head = {'Referer': 'https://m.pge.com/index.html', 'User-Agent': 'Mozilla/5.0'}
    resp = sess.get(url, params=qs, headers=head, timeout=31)
    resp.raise_for_status()

    # continue SAML auth (origin: sso2.opower.com)
    m = re.search(r'action="(.*?)"', resp.text)
    url = m.group(1)
    doc = {m.group(1): html.unescape(m.group(2).replace('\n', '').replace('\r', '')) for m in re.finditer(r'(?mis)name="(.*?)"\s*value="(.*?)"', resp.text)}
    #print("SAML 2: %r %r" % (url, doc))
    headers = {'Referer': 'https://www.pge.com/affwebservices/public/saml2sso?SPID=sso.opower.com&RelayState=https%3A%2F%2Fpge.opower.com%2Fei%2Fapp%2Fr%2Fenergy-usage-details'}
    resp = sess.post(url, data=doc, headers=headers, timeout=31)
    resp.raise_for_status()

    # finish SAML auth (origin: pge.opower.com)
    m = re.search(r'<form.*?action="(.*?)"', resp.text)
    url = m.group(1)
    doc = {m.group(1): html.unescape(m.group(2).replace('\n', '').replace('\r', '')) for m in re.finditer(r'(?mis)<input.*?name="(.*?)"\s*value="(.*?)"', resp.text)}
    #print("SAML 3: %r %r" % (url, doc))
    headers = {'Referer': 'https://sso2.opower.com/'}
    resp = sess.post(url, data=doc, headers=headers, timeout=31)
    resp.raise_for_status()

    # get account IDs
    url = 'https://pge.opower.com/ei/edge/apis/DataBrowser-v1/metadata?preferredUtilityAccountIdType=UTILITY_ACCOUNT_ID_1'
    qs = {}
    resp = sess.get(url, params=qs, timeout=31)
    try:
        resp.raise_for_status()
    except Exception:
        print(resp.text)
        raise
    auid = resp.json()['fuelTypeServicePoint']['ELECTRICITY'][0]['accountUuid']

    try:
        start_date = sys.argv[1]
    except IndexError:
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(30)).isoformat()

    try:
        end_date = sys.argv[2]
    except IndexError:
        end_date = (datetime.datetime.utcnow()).isoformat()

    # get usage data
    url = "https://pge.opower.com/ei/edge/apis/DataBrowser-v1/usage/utilityAccount/" + str(auid)
    qs = {
        "startDate":start_date,
        "endDate":end_date,
        "aggregateType":"hour",
    }
    resp = sess.get(url, params=qs, timeout=31)
    resp.raise_for_status()
    js = resp.json()
    for r in js['reads']:
        print(r['startTime'], r['value'])

if __name__ == '__main__':
    main()
