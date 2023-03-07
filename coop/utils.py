from messaging.utils import sendSMS
from conf.utils import log_debug, log_error
from coop.models import Cooperative

def sendMemberSMS(request, member, message):
    if member.cooperative.send_message:
        msisdn = member.phone_number
        try:
            log_debug('Message: %s Receiver: %s' % (message, msisdn))
            sendSMS(request, msisdn, message)
            
            return True
        except Exception:
            log_error()
            return False
    return False


def check_coop_url(str):
    coop = Cooperative.objects.filter(system_url__icontains=str)
    if coop.exists():
        coop = coop[0]
    return coop
