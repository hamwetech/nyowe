import xmlrpclib
from django.conf import settings
from datetime import datetime, date

settings.configure()
ITDB="nyowe"
ITUSERNAME="apiuser@nyowe.tecthings.it"
ITPASSWORD="2cd696a66b01dcbc3d2c32ab7ccaedcb735283f3"
ITURL="https://nyowe.techthings.it"



if __name__ == "__main__":
    # Specify the url for the odoo system to connect to for example
    #https://www.odoo.com
    url = ITURL
    # Specify the database name for the odoo system to connect to for example nyowe
    db = ITDB
    # Set the credentials eg the username and api key
    # The username is a valid user login used to connect to the odoo system eg
    #smsapiuser
    username = ITUSERNAME
    # Specify the api key
    password = ITPASSWORD
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
    [{'phone_no':"+256752444902",'record_from':'external_api','message':"This is a message from external api updated"}])

