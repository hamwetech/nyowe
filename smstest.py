import xmlrpc.client
from datetime import datetime, date
if __name__ == "__main__":
    # Specify the url for the odoo system to connect to for example
    url = "https://nyowetest.techthings.it"
    # Specify the database name for the odoo system to connect to for example nyowe
    db = "nyowetest"
    # Set the credentials eg the username and api key
    # The username is a valid user login used to connect to the odoo system eg
    username = 'test@nyowetest.techthings.it'
    # Specify the api key
    password = "0ff925894fd38348c9b0109f58e3b708cd5b1c41"
    # This is for getting the version of odoo and the server
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    response = common.version()
    print(response)
    # Authenticate with logins returns the id of the authenticated user
    uid = common.authenticate(db, username, password, {})
    print(uid)
    # setup the models
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    # Call the method on the model for sending the SMS
    # In this example we use the model as "odoo.tt.sms",
    # The method is send_msg_from_api
    # and pass in an array of a dictionary as an argument as specified below
    create_msg = models.execute_kw(db, uid, password, 'odoo.tt.sms',
    'send_msg_from_api',
    [{'phone_no':"+256752444902",'record_from':'external_api','message':"This is a message from external api updated"}])
