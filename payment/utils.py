import re
import traceback
import logging
import sys
import unicodedata
import requests
import base64
import json
from django.conf import settings
from datetime import datetime
from conf.utils import log_debug, log_error

def payment_transction(msisdn, amount, reference):
        # if True:
        #     return {"status": "FAILED", "statusMessage": "Test Complete"}
        msisdn = msisdn
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = settings.HPPASSWORD #'W3E4g8weR5TgH0Td2344'
        accountid = settings.HPACCOUNTID #'andrew'
        token = base64.urlsafe_b64encode(accountid + password + timestamp)
        http_auth = base64.urlsafe_b64encode(settings.HPHTTPAUTH)
        # url = 'https://hamwepay.com/endpoint/service/transaction/'
        url = 'https://payments.hamwepay.com/endpoint/service/transaction/'

        try:
            data = {
                "reference": reference,
                "method": "PAYOUT",
                "amount": "%s" % amount,
                "timestamp": timestamp,
                "token": token,
                "phonenumber": msisdn,
                "accountid": accountid
            }

            log_debug("Sending trx: %s" % data)
            print("Sending trx: %s" % data)
            headers = {'content-type': 'application/json', 'Authorization': 'Basic %s' % http_auth}

            req = requests.post(url, data=json.dumps(data), headers=headers)
            print(req.text)
            jr = json.loads(req.text)
            if 'transactionStatus' in jr:
                if jr['transactionStatus'] == 'SUCCESSFUL':
                    log_debug(jr)
            log_debug("Response From Server %s" % req.text)
            return jr
        except Exception as err:
            log_error()
            return {"status": "ERROR", "statusMessage": "Server Error"}