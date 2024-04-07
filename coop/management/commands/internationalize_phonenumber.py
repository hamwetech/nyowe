from django.core.management.base import BaseCommand, CommandError
from conf.utils import get_consontant_upper, generate_numeric, internationalize_number
from coop.models import Cooperative, CooperativeMember
from account.models import Account


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        members = CooperativeMember.objects.all()
        for member in members:
            if member.phone_number:
                phn = internationalize_number(member.phone_number)
                member.phone_number = phn
                member.save()
                print("Member phone number updated %s " % phn)