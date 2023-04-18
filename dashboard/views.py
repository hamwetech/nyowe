# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.db.models import Sum
from django.views.generic import TemplateView
from django.db.models import Q, CharField, Max, Value as V
from django.db.models.functions import Concat
from coop.models import *
from activity.models import *
from payment.models import *
from product.models import ProductVariationPrice
from messaging.models import OutgoingMessages

class DashboardView(TemplateView):
    template_name = "dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        cooperatives = Cooperative.objects.all()
        farmer_group = FarmerGroup.objects.all()
        members = CooperativeMember.objects.all()
        agents = Profile.objects.filter(access_level__name='AGENT')
        cooperative_contribution = CooperativeContribution.objects.all().order_by('-update_date')[:5]
        cooperative_shares = CooperativeShareTransaction.objects.all().order_by('-update_date')
        product_price = ProductVariationPrice.objects.all().order_by('-update_date')
        collections = Collection.objects.all().order_by('-update_date')
        payments = MemberPaymentTransaction.objects.all().order_by('-transaction_date')
        success_payments = payments.filter(status='SUCCESSFUL')
        training = TrainingSession.objects.all().order_by('-create_date')
        # supply_requests = MemberSupplyRequest.objects.all().order_by('-create_date')
        # supply_requests = supply_requests.filter(status='ACCEPTED')
        m_shares = CooperativeMemberSharesLog.objects
        messages = OutgoingMessages.objects.all()

        if not self.request.user.profile.is_union():
            if hasattr(self.request.user, 'cooperative_admin'):
                
                coop_admin = self.request.user.cooperative_admin.cooperative
                members = members.filter(cooperative = coop_admin)
                cooperative_shares = cooperative_shares.filter(cooperative = coop_admin)
                m_shares = m_shares.filter(cooperative_member__cooperative = coop_admin)
                collections = collections.filter(member__cooperative = coop_admin)
        collection_qty = collections.aggregate(total_amount=Sum('quantity'))
        total_payment = success_payments.aggregate(total_amount=Sum('amount'))
        collection_amt = collections.aggregate(total_amount=Sum('total_price'))
        members_shares = members.aggregate(total_amount=Sum('shares'))
        savings_balance = members.aggregate(total_amount=Sum('savings_balance'))
        eighteen = [f for f in members if f.age if f.age <= 18]
        youth = [f for f in members if f.age if f.age > 15 and f.age <= 25]
        midlife = [f for f in members if f.age if f.age > 25]
        male = members.filter(Q(gender='male') | Q(gender='m'))
        female = members.filter(Q(gender='female') | Q(gender='f'))
        with_phones = members.filter(own_phone=True)
        male_phones = male.filter(own_phone=True)
        female_phones = female.filter(own_phone=True)
        # members_animals = members.aggregate(total_amount=Sum('animal_count'))



        shares = cooperatives.aggregate(total_amount=Sum('shares'))
        m_shares = m_shares.values('cooperative_member',
                                   name=Concat('cooperative_member__surname',
                                               V(' '),
                                               'cooperative_member__first_name'
                                               ),
                                   
                                   ).annotate(total_amount=Sum('amount'), total_shares=Sum('shares'), transaction_date=Max('transaction_date')).order_by('-transaction_date')
        
        cooperative_shares = cooperative_shares.values('cooperative',
                                   'cooperative__name',
                                   ).annotate(total_amount=Sum('amount_paid'), total_shares=Sum('shares_bought'), transaction_date=Max('transaction_date')).order_by('-transaction_date')

        is_refugee = members.filter(is_refugee=True)

        context['cooperatives'] = cooperatives.count()
        context['farmer_group'] = farmer_group.count()

        context['shares'] = shares['total_amount']
        context['transactions'] = Cooperative.objects.all().count()
        context['members'] = members.count()
        context['eighteen'] = len(eighteen)
        context['youth'] = len(youth)
        context['midlife'] = len(midlife)
        context['male'] = male.count()
        context['female'] = female.count()
        context['with_phones'] = with_phones.count()
        context['male_phones'] = male_phones.count()
        context['female_phones'] = female_phones.count()
        context['agents'] = agents.count()



        context['is_refugee'] = is_refugee.count()
        context['active'] = ['_dashboard', '']
        context['members_shares'] = members_shares['total_amount']
        context['savings_balance'] = savings_balance['total_amount']
        context['m_shares'] = m_shares[:5]
        context['collections_latest'] = collections[:5]
        context['collections'] = collection_qty['total_amount']
        context['collection_amt'] = collection_amt['total_amount']
        context['total_payment'] = total_payment['total_amount']
        
        context['cooperative_contribution'] = cooperative_contribution
        context['cooperative_shares'] = cooperative_shares[:5]
        context['training'] = training[:5]
        context['product_price'] = product_price
        context['sms'] = messages.filter(status='SENT').count()
        # context['supply_requests'] = supply_requests[:5]
        return context
    
    


