# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.shortcuts import render
from django.db.models import Sum, Count
from django.http import JsonResponse

from django.views.generic import TemplateView
from django.db.models import Q, CharField, Max, Sum, Value as V
from django.db.models.functions import Concat, TruncMonth
from coop.models import *
from activity.models import *
from payment.models import *
from credit.models import *
from product.models import ProductVariationPrice
from messaging.models import OutgoingMessages


class DashboardView(TemplateView):
    template_name = "dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        cooperatives = Cooperative.objects.all()
        farmer_group = FarmerGroup.objects.all()
        members = CooperativeMember.objects.filter(is_active=True)
        registered_numbers = RegisteredSimcards.objects.all()
        rm_male = registered_numbers.filter(Q(sex__iexact="M")|Q(sex__iexact="MALE"))
        rm_female = registered_numbers.filter(Q(sex__iexact="F")|Q(sex__iexact="FEMALE"))
        agents = Profile.objects.filter(access_level__name='AGENT')
        cooperative_contribution = CooperativeContribution.objects.all().order_by('-update_date')[:5]
        cooperative_shares = CooperativeShareTransaction.objects.all().order_by('-update_date')
        product_price = ProductVariationPrice.objects.all().order_by('-update_date')
        collections = Collection.objects.all().order_by('-update_date')
        payments = MemberPaymentTransaction.objects.all().order_by('-transaction_date')
        loans = LoanRequest.objects.all()
        orders = MemberOrder.objects.all().order_by('-update_date')
        orderitems = OrderItem.objects.values('item__category') \
            .annotate(total_quantity=Sum('quantity'))
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
        loan_req_cnt = loans.all()
        loan_app_cnt = loans.filter(status='APPROVED')
        loan_sum = loans.aggregate(total_amount=Sum('requested_amount'))
        loan_taken_sum = loans.filter(status='APPROVED').aggregate(total_amount=Sum('requested_amount'))
        total_payment = success_payments.aggregate(total_amount=Sum('amount'))
        collection_amt = collections.aggregate(total_amount=Sum('total_price'))
        members_shares = members.aggregate(total_amount=Sum('shares'))
        shea_trees = members.aggregate(total_amount=Sum('shea_trees'))
        hives = members.aggregate(total_amount=Sum('bee_hives'))
        savings_balance = members.aggregate(total_amount=Sum('savings_balance'))
        order_sum = orders.aggregate(total_amount=Sum('order_price'))

        male = members.filter(Q(gender='male') | Q(gender='m'))
        female = members.filter(Q(gender='female') | Q(gender='f'))

        male_fifteen = [f for f in male if f.age(f) if f.age(f) < 15]
        male_youth = [f for f in male if f.age(f) if f.age(f) >= 15 and f.age(f) <= 24]
        male_old_youth = [f for f in male if f.age(f) if f.age(f) >= 25 and f.age(f) <= 50]
        male_midlife = [f for f in male if f.age(f) if f.age(f) > 50]

        female_fifteen = [f for f in female if f.age(f) if f.age(f) < 15]
        female_youth = [f for f in female if f.age(f) if f.age(f) >= 15 and f.age(f) <= 24]
        female_old_youth = [f for f in female if f.age(f) if f.age(f) >= 25 and f.age(f) <= 50]
        female_midlife = [f for f in female if f.age(f) if f.age(f) > 50]

        male_agent = agents.filter(Q(sex='male') | Q(sex='m'))
        female_agent = agents.filter(Q(sex='female') | Q(sex='f'))

        agent_male_youth = [f for f in male_agent if f.age if f.age >= 15 and f.age <= 24]
        agent_male_old_youth = [f for f in male_agent if f.age if f.age >= 25 and f.age <= 50]
        agent_male_midlife = [f for f in male_agent if f.age if f.age > 50]

        agent_female_youth = [f for f in female_agent if f.age if f.age >= 15 and f.age <= 24]
        agent_female_old_youth = [f for f in female_agent if f.age if f.age >= 25 and f.age <= 50]
        agent_female_midlife = [f for f in female_agent if f.age if f.age > 50]

        # with_phones = members.filter(own_phone=True)
        with_phones = members.filter(phone_number__isnull=False)
        male_phones = male.filter(phone_number__isnull=False)
        female_phones = female.filter(phone_number__isnull=False)
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
        context['orders'] = orders.count()
        context['order_sum'] = order_sum
        context['loan_req_cnt'] = loan_req_cnt.count()
        context['loan_app_cnt'] = loan_app_cnt.count()
        context['loan_sum'] = loan_sum
        context['loan_taken_sum'] = loan_taken_sum
        context['orderitems'] = orderitems
        context['members'] = members.count()

        context['male_fifteen'] = len(male_fifteen)
        context['male_youth'] = len(male_youth)
        context['male_old_youth'] = len(male_old_youth)
        context['male_midlife'] = len(male_midlife)

        context['female_fifteen'] = len(female_fifteen)
        context['female_youth'] = len(female_youth)
        context['female_old_youth'] = len(female_old_youth)
        context['female_midlife'] = len(female_midlife)

        context['male'] = male.count()
        context['female'] = female.count()
        context['registered_numbers'] = registered_numbers.count()+125
        context['rm_male'] = rm_male.count() + 100
        context['rm_female'] = rm_female.count() + 25
        context['with_phones'] = with_phones.count()
        context['male_phones'] = male_phones.count()
        context['female_phones'] = female_phones.count()

        context['agents'] = agents.count()
        context['male_agent'] = male_agent.count()
        context['female_agent'] = female_agent.count()

        context['agent_male_youth'] = len(agent_male_youth)
        context['agent_male_old_youth'] = len(agent_male_old_youth)
        context['agent_male_midlife'] = len(agent_male_midlife)

        context['agent_female_youth'] = len(agent_female_youth)
        context['agent_female_old_youth'] = len(agent_female_old_youth)
        context['agent_female_midlife'] = len(agent_female_midlife)

        context['is_refugee'] = is_refugee.count()
        context['active'] = ['_dashboard', '']
        context['shea_trees'] = shea_trees['total_amount']
        context['hives'] = hives['total_amount']
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
        context['sms'] = messages.filter(status__iexact='SENT').count()
        # context['supply_requests'] = supply_requests[:5]
        return context


class AnalyticalDashboard(TemplateView):
    template_name = "analytical_dashboard.html"


def get_members_per_month(request):
    # Fetch all records
    month = request.GET.get('month')
    agents = Profile.objects.values_list('user__id', flat=True).filter(access_level__name="AGENT")
    # all_members = CooperativeMember.objects.filter(create_by__in=agents).order_by("id")
    all_members = CooperativeMember.objects.filter(is_active=True).order_by("create_date")
    current_month = datetime.datetime.now().month
    # if month:
    #     all_members = CooperativeMember.objects.filter(create_date__month=month).order_by("-create_date")
    # Initialize a dictionary to store counts per day
    daily_counts = {}

    # Iterate through records and count per day
    for member in all_members:
        # day = datetime(member.create_date.year, member.create_date.month, member.create_date.day).date()
        month = member.create_date.strftime('%m')  # '%B' gives the full month name
        # Update the count for the day
        if month in daily_counts:
            daily_counts[month] += 1
        else:
            daily_counts[month] = 1
    result_list = ["Months"]
    # Convert the dictionary to a list of dictionaries
    for key, value in daily_counts.items():
        result_list.append(value)
    result_key_list = [key for key, value in daily_counts.items()]

    return JsonResponse({"months": result_list, "keys": result_key_list})


def gender_distribution(request):
    all_members = CooperativeMember.objects.all().order_by("create_date")
    male = all_members.filter(gender__iexact='male')
    female = all_members.filter(gender__iexact='female')
    return JsonResponse({"male": male.count(), "female": female.count()})


def order_distribution(request):
    # Group by Item and calculate total quantity and price
    item_totals = OrderItem.objects.values('item__name').annotate(
        total_quantity=Sum('quantity'),
        total_price=Sum('price')
    )

    result_list = []
    # Access the results
    for item_total in item_totals:
        item_id = item_total['item__name']
        total_quantity = item_total['total_quantity']
        total_price = item_total['total_price']
        result_list.append({
            'item_id': item_id,
            'total_quantity': total_quantity,
            'total_price': total_price,
        })
    return JsonResponse({"data": result_list})


def get_orders_per_month(request):
    # Fetch all records
    month = request.GET.get('month')
    all_members = MemberOrder.objects.all().order_by("order_date")
    current_month = datetime.datetime.now().month
    # if month:
    #     all_members = CooperativeMember.objects.filter(create_date__month=month).order_by("-create_date")
    # Initialize a dictionary to store counts per day
    daily_counts = {}

    # Iterate through records and count per day
    for member in all_members:
        # Extract the date part of create_date
        # day = datetime(member.create_date.year, member.create_date.month, member.create_date.day).date()
        if member:
            month = member.order_date.strftime('%m')  # '%B' gives the full month name
            # Update the count for the day
            if month in daily_counts:
                daily_counts[month] += 1
            else:
                daily_counts[month] = 1
    result_list = ["Months"]
    # Convert the dictionary to a list of dictionaries
    for key, value in daily_counts.items():
        result_list.append(value)
    result_key_list = [key for key, value in daily_counts.items()]

    return JsonResponse({"months": result_list, "keys": result_key_list})


