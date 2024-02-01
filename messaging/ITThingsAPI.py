import xmlrpclib
from django.conf import settings
from datetime import datetime, date


class MessagingTransaction():

    url = None
    db = None
    username = None
    password = None


    def __init__(self):
        self.url = settings.ITURL
        self.db = settings.ITDB
        self.username = settings.ITUSERNAME
        self.password = settings.ITPASSWORD
        self.user = user

    def send_sms(self, message, msisdn):
        # Specify the url for the odoo system to connect to for example
        #https://www.odoo.com
        url = self.url
        # Specify the database name for the odoo system to connect to for example nyowe
        db = self.db
        # Set the credentials eg the username and api key
        # The username is a valid user login used to connect to the odoo system eg
        #smsapiuser
        username = self.username
        # Specify the api key
        password = self.password
        # This is for getting the version of odoo and the server
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
        response = common.version()
        print(response)
        # Authenticate with logins returns the id of the authenticated user
        uid = common.authenticate(db, username, password, {})
        print(uid)
        # setup the models
        models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
        # Call the method on the model for sending the SMS
        # In this example we use the model as "odoo.tt.sms",
        # The method is send_msg_from_api
        # and pass in an array of a dictionary as an argument as specified below
        create_msg = models.execute_kw(db, uid, password, 'odoo.tt.sms',
        'send_msg_from_api',
        [{'phone_no': msisdn,'record_from':'external_api','message': message}])

