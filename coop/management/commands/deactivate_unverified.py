from django.core.management.base import BaseCommand, CommandError
from conf.utils import get_consontant_upper, generate_numeric, internationalize_number
from coop.models import Cooperative, CooperativeMember
from account.models import Account


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        members = CooperativeMember.objects.all()
        for member in members:
            if member.verified_record:
                member.is_active = True
            else:
                member.is_active = False
            member.save()
            print("Member Status updated %s: %s " % (member, member.is_active))