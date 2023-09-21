from django.core.management.base import BaseCommand
from django.db import transaction
from payment.models import MemberPayment, MemberPaymentTransaction, MobileMoneyRequest
from coop.models import CooperativeMember
from coop.views.member import save_transaction
from django.conf import settings

from payment.HamwePay import HamwePay
from conf.utils import log_debug, log_error


class Command(BaseCommand):
    help = 'Check the status of a transaction'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                mmrequest = MobileMoneyRequest.objects.filter(status='PENDING')
                for mm in mmrequest:
                    reference = mm.response_reference
                    credentials = {
                        'password': settings.HPPASSWORD,# 'W3E4g8weR5TgH0Td2344',
                        'accountid': settings.HPACCOUNTID,#'andrew',
                        'http_credentials': settings.HPHTTPAUTH,#'andrew:hamwe'
                    }
                    hamwepay = HamwePay(credentials)
                    response = hamwepay.check_status(reference)
                    if 'status' in response:
                        status = response['status']
                        statusMessage = response['statusMessage']
                        if status == 'OK':
                            mm.status = 'SUCCESSFUL'
                            mm.save()
                            mtrx = MemberPaymentTransaction.objects.filter(transaction_reference=mm.transaction_reference)
                            if mtrx.exists():
                                membert = mtrx[0]
                                membert.status = "SUCCESSFUL"
                                membert.save()

                                amount = membert.amount
                                member = membert.member
                                params = {'amount': amount,
                                          'member': member,
                                          'transaction_reference': membert.transaction_reference,
                                          'transaction_type': 'PAYOUT',
                                          'entry_type': 'DEBIT',
                                          'status': 'SUCCESS'
                                          }
                                member = CooperativeMember.objects.filter(pk=member.id)
                                if member.exists():
                                    member = member[0]
                                    paid = member.paid_amount
                                    member.paid_amount = paid + amount
                                    member.save()
                                save_transaction(params)

                    self.stdout.write(self.style.SUCCESS('Response: %s' % response))
        except Exception as e:
            self.stdout.write(self.style.SUCCESS('Error occured %s' % e))
            log_error()
