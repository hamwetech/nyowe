# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import csv
import magic
import re
import xlrd
import xlwt
import time
from datetime import datetime
import json
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, CharField, Max, Value as V
from django.db.models.functions import Concat
from django.utils.encoding import smart_str
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.views.generic import View, ListView, DetailView, TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormMixin, FormView
from django.forms.formsets import formset_factory, BaseFormSet

from messaging.utils import sendSMS
from coop.utils import sendMemberSMS
from conf.utils import log_debug, log_error, internationalize_number, generate_alpanumeric, float_to_intstring, genetate_uuid4, get_deleted_objects,\
get_message_template as message_template
from coop.models import *
from activity.models import TrainingAttendance
from product.models import Product, ProductVariation, ProductUnit
from coop.forms import *
from account.models import Account, AccountTransaction

from payment.HamwePay import HamwePay


class ExtraContext(object):
    extra_context = {}

    def get_context_data(self, **kwargs):
        context = super(ExtraContext, self).get_context_data(**kwargs)
        context['active'] = ['_coop_member']
        context['title'] = 'Coop'
        context.update(self.extra_context)
        return context


class MemberDeleteView(ExtraContext, DeleteView):
    model = CooperativeMember
    success_url = reverse_lazy('coop:member_list')
    
    def get_context_data(self, **kwargs):
        #
        context = super(MemberDeleteView, self).get_context_data(**kwargs)
        #
        
        deletable_objects, model_count, protected = get_deleted_objects([self.object])
        #
        context['deletable_objects']=deletable_objects
        context['model_count']=dict(model_count).items()
        context['protected']=protected
        #
        return context


class MemberCreateView(ExtraContext, CreateView):
    template_name = 'coop/memberprofile_form.html'
    model = CooperativeMember
    form_class = MemberProfileForm
    success_url = reverse_lazy('coop:member_list')
    
    def get_form_kwargs(self):
        kwargs = super(MemberCreateView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs
    
    def form_valid(self, form):
        try:
            form.instance.member_id = self.generate_member_id(form.instance.cooperative)
            form.instance.create_by = self.request.user
            member = super(MemberCreateView, self).form_valid(form)
        except Exception as e:
            # form.add_error(None, 'The Phone Number %s exists. Please provide another.' % form.instance.phone_number)
            import traceback
            print(traceback.format_exc())
            form.add_error(None, e)
            return super(MemberCreateView, self).form_invalid(form)
        try:
            
            message = message_template().member_registration
            if message:
                if re.search('<NAME>', message):
                    if member.surname:
                        message = message.replace('<NAME>', '%s %s' % (member.surname.title(), member.first_name.title()))
                    message = message.replace('<COOPERATIVE>', member.cooperative.name)
                    message = message.replace('<IDNUMBER>', member.member_id)
                sendMemberSMS(request, member, message)
        except Exception as e:
            log_error()
            pass
        return member
    
    def generate_member_id(self, cooperative):
        member = CooperativeMember.objects.all()
        count = member.count() + 1
        
        today = datetime.today()
        datem = today.year
        yr = str(datem)[2:]
        # idno = generate_numeric(size=4, prefix=str(m.cooperative.code)+yr)
        # fint = "%04d"%count
        # idno = str(cooperative.code)+yr+fint
        # member = member.filter(member_id=idno)
        if cooperative:
            idno = self.check_id(member, cooperative, count, yr)
            log_debug("Cooperative %s code is %s" % (cooperative.code, idno))
        else:
            idno = self.check_id_nc(member, count, yr)
        return idno
    
    def check_id(self, member, cooperative, count, yr):
        fint = "%04d"%count
        idno = str(cooperative.code)+yr+fint
        member = member.filter(member_id=idno)
        if member.exists():
            count = count + 1
            #print "iteration count %s" % count
            return self.check_id(member, cooperative, count, yr)
        return idno

    def check_id_nc(self, member, count, yr):
        rnd = generate_alpanumeric(size=3).upper()
        fint = "%04d"%count
        idno = rnd+yr+fint
        member = member.filter(member_id=idno)
        if member.exists():
            count = count + 1
            #print "iteration count %s" % count
            return self.check_id_nc(member, count, yr)
        return idno


class MemberUpdateView(ExtraContext, UpdateView):
    template_name = 'coop/memberprofile_form.html'
    model = CooperativeMember
    form_class = MemberProfileForm
    success_url = reverse_lazy('coop:member_list')
    
    def get_form_kwargs(self):
        kwargs = super(MemberUpdateView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs
    
    
def save_transaction(params):
        amount = params.get('amount')
        member = params.get('member')
        transaction_reference = params.get('transaction_reference')
        transaction_type = params.get('transaction_type')
        entry_type = params.get('entry_type')
        bal_before = 0
        tq = MemberTransaction.objects.all().order_by('-id')
        if tq.exists():
            bal_before = tq[0].balance_after
        if entry_type == "CREDIT":
            new_bal = amount + bal_before
        if entry_type == "DEBIT":
            new_bal = bal_before - amount
        MemberTransaction.objects.create(
            member = member,
            transaction_type = transaction_type,
            entry_type = entry_type,
            transaction_reference = transaction_reference,
            balance_before = bal_before,
            amount = amount,
            balance_after = new_bal,
        )
        # CooperativeMember.objects.filter(pk=member.id).update(collection_amount=new_bal)
        log_debug("Saved")
        
               
def load_villages(request):
    sub_county_id = request.GET.get('sub_county')
    villages = Parish.objects.filter(sub_county=sub_county_id).order_by('name')
    return render(request, 'coop/village_dropdown_list_options.html', {'villages': villages})


def load_coop_members(request):
    cooperative_id = request.GET.get('cooperative')
    members = dict()
    if cooperative_id: 
        members = CooperativeMember.objects.filter(cooperative=cooperative_id).order_by('first_name')
    return render(request, 'coop/member_dropdown_list_options.html', {'members': members})

def load_fg_members(request):
    fg_id = request.GET.get('farmer_group')
    members = dict()
    if fg_id:
        members = CooperativeMember.objects.filter(farmer_group=fg_id).order_by('first_name')
    return render(request, 'coop/member_dropdown_list_options.html', {'members': members})

def load_fg_member(request):
    m_id = request.GET.get('member')
    amount = 0
    phone_number = ""
    if m_id:
        try:
            members = CooperativeMember.objects.get(pk=m_id)
            phone_number = members.phone_number
            amount = members.collection_amount - members.paid_amount
        except Exception as e:
            print(e)
            amount = 0
            phone_number = ""

    return JsonResponse({"amount": amount, "phone_number": phone_number}, safe=False)


class MemberUploadExcel(ExtraContext, View):
    template_name = 'coop/upload_member.html'
    
    def get(self, request, *args, **kwargs):
        data = dict()
        data['form'] = MemberUploadForm
        return render(request, self.template_name, data)
    
    def post(self, request, *args, **kwargs):
        data = dict()
        form = MemberUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['excel_file']
            
            path = f.temporary_file_path()

            index = int(form.cleaned_data['sheet'])-1
            startrow = int(form.cleaned_data['row'])-1
            farmer_name_col = int(form.cleaned_data['farmer_name_col'])
            identification_col = int(form.cleaned_data['identification_col'])
            gender_col = int(form.cleaned_data['gender'])
            date_of_birth_col = int(form.cleaned_data['date_of_birth_col'])
            phone_number_col = int(form.cleaned_data['phone_number_col'])
            role_col = int(form.cleaned_data['role_col'])
            acreage_col = int(form.cleaned_data['acreage_col'])
            # cotton_col = int(form.cleaned_data['cotton_col'])
            # soya_col = int(form.cleaned_data['soya_col'])
            # soghum_col = int(form.cleaned_data['soghum_col'])
            cooperative_col = int(form.cleaned_data['cooperative_col'])
            district_col = int(form.cleaned_data['district_col'])
            county_col = int(form.cleaned_data['county_col'])
            sub_county_col = int(form.cleaned_data['sub_county_col'])
            parish_col = int(form.cleaned_data['parish_col'])
            village_col = int(form.cleaned_data['village_col'])
            user_id_col = int(form.cleaned_data['user_id_col'])
            shea_trees_col = int(form.cleaned_data['shea_trees_col'])
            harvested_quantity_col = int(form.cleaned_data['harvested_quantity_col'])
            sunflower_acreage_col = int(form.cleaned_data['sunflower_acreage_col'])
            sunflower_planted_col = int(form.cleaned_data['sunflower_planted_col'])
            sunflower_collected_col = int(form.cleaned_data['sunflower_collected_col'])

            book = xlrd.open_workbook(filename=path, logfile='/tmp/xls.log')
            sheet = book.sheet_by_index(index)

            # check if RECORDID column exists
            column_row = [str(sheet.cell_value(0, col)) for col in range(sheet.ncols)]  # Header
            record_id_col = column_row.index('RecordID') if 'RecordID' in column_row else None
            verified_record_col = column_row.index('VERIFIED_RECORD') if 'VERIFIED_RECORD' in column_row else None

            rownum = 0
            data = dict()
            member_list = []
            for i in range(startrow, sheet.nrows):
                try:
                    row = sheet.row(i)
                    rownum = i+1

                    # get record ID if any

                    record_id = re.sub("[^0-9]", "", row[record_id_col].value) if record_id_col else None
                    try:
                        if record_id is not None:
                            record_id = int(record_id)
                    except ValueError:
                        data['errors'] = '"%s" is not a valid RecordID (row %d)' % (row[record_id_col].value, i + 1)
                        return render(request, self.template_name, {'active': 'system', 'form': form, 'error': data})

                    # get verified_value ID if any
                    verified_record = re.sub("[^0-9]", "", row[verified_record_col].value) if record_id_col else 0
                    try:
                        if verified_record is not None:
                            if int(verified_record) in [0, 1]:
                                verified_record = int(verified_record)
                            else:
                                raise ValueError
                    except ValueError:
                        data['errors'] = '"%s" is not a valid value!, VERIFIED_RECORD column inputs must be either 1(for true/verified records) or 0(for false/unverified records) or blank(for unclassified records).  see (row %d).' % (row[verified_record_col].value, i + 1)
                        return render(request, self.template_name, {'active': 'system', 'form': form, 'error': data})

                    farmer_name = smart_str(row[farmer_name_col].value).strip()
                    if not re.search('^[A-Z0-9\s\(\)\-\.\/\']+$', farmer_name, re.IGNORECASE):
                        if (i+1) == sheet.nrows: break
                        data['errors'] = '"%s" is not a valid Farmer (row %d)' % \
                        (farmer_name, i+1)
                        return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})
                    
                    gender = smart_str(row[gender_col].value).strip()
                    if not re.search('^[A-Z\s\(\)\-\.]+$', gender, re.IGNORECASE):
                        data['errors'] = '"%s" is not a valid Gender (row %d)' % \
                        (gender, i+1)
                        return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})

                    identification = smart_str(row[identification_col].value).strip()
                    if identification:
                        if not re.search('^[A-Z\s\(\)\-\.]+$', gender, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Identification Number (row %d)' % \
                            (identification, i+1)
                            return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})
               
                    date_of_birth = (row[date_of_birth_col].value)
                    if date_of_birth:
                        try:
                            #print(date_of_birth)
                            date_str = datetime(*xlrd.xldate_as_tuple(date_of_birth, book.datemode))
                            date_of_birth = date_str.strftime("%Y-%m-%d")
                        except Exception as e:
                            data['errors'] = '"%s" is not a valid Date of Birth (row %d): %s' % \
                            (date_of_birth, i+1, e)
                            return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})

                    phone_number = (row[phone_number_col].value)
                    if phone_number:
                        try:
                            phone_number = int(phone_number)
                        except Exception as e:
                            phone_number = None

                        if phone_number:
                            if not re.search('^[0-9]+$', str(phone_number), re.IGNORECASE):
                                data['errors'] = '"%s" is not a valid Phone Number (row %d)' % (phone_number, i+1)
                                return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})

                    role = smart_str(row[role_col].value).strip()
                    if role:
                        if not re.search('^[A-Z\s\(\)\-\.]+$', role, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Role (row %d)' % (role, i+1)
                            return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})
                    
                    acreage = smart_str(row[acreage_col].value).strip()
                    if not re.search('^[0-9\.]+$', acreage, re.IGNORECASE):
                        data['errors'] = '"%s" is not a valid Acreage (row %d)' % (acreage, i+1)
                        return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})
                    
                    # soya = smart_str(row[soya_col].value).strip()
                    # if not re.search('^[0-9\.]+$', soya, re.IGNORECASE):
                    #     data['errors'] = '"%s" is not a valid Soya Acreage (row %d)' % \
                    #     (soya, i+1)
                    #     return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})
                    #
                    # soghum = smart_str(row[soghum_col].value).strip()
                    # if not re.search('^[0-9\.]+$', soghum, re.IGNORECASE):
                    #     data['errors'] = '"%s" is not a valid Soghum Acreage (row %d)' % \
                    #     (soya, i+1)
                    #     return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})

                    cooperative = smart_str(row[cooperative_col].value).strip()
                    if cooperative:
                        if not re.search('^[A-Z\s\(\)\-\.\/'']+$', cooperative, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Cooperative (row %d)' % (cooperative, i+1)
                            return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})

                        try:
                            cooperative = Cooperative.objects.get(name=cooperative)
                        except Exception as e:
                            log_error()
                            data['errors'] = 'Cooperative "%s" Not found (row %d)' % (cooperative, i+1)
                            return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})

                    district = smart_str(row[district_col].value).strip()
                    if district:
                        if not re.search('^[A-Z\s\(\)\-\.]+$', district, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid District (row %d)' % (district, i+1)
                            return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})
                    
                    county = smart_str(row[county_col].value).strip()
                    if county:
                        if not re.search('^[A-Z\s\(\)\-\.]+$', county, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid County (row %d)' % (county, i+1)
                            return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})    
                    
                    sub_county = smart_str(row[sub_county_col].value).strip()
                    if sub_county:
                        if not re.search('^[A-Z\s\(\)\-\.]+$', sub_county, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Sub County (row %d)' % (sub_county, i+1)
                            return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})
                    
                    parish = smart_str(row[parish_col].value).strip()
                    if parish:
                        if not re.search('^[A-Z\s\(\)\-\.]+$', parish, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Parish (row %d)' % (parish, i+1)
                            return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})
                   
                    village = smart_str(row[village_col].value).strip()
                    if village:
                        if not re.search('^[A-Z0-9\s\(\)\-\.]+$', village, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Village (row %d)' % (village, i+1)
                            return render(request, self.template_name, {'active': 'system', 'form':form, 'error': data})

                    user_id = smart_str(row[user_id_col].value).strip()
                    if user_id:
                        if not re.search('^[A-Z0-9\s\(\)\-\.]+$', user_id, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid USer ID (row %d)' % (user_id, i + 1)
                            return render(request, self.template_name,
                                          {'active': 'system', 'form': form, 'error': data})

                    shea_trees = smart_str(row[shea_trees_col].value).strip()
                    if shea_trees:
                        if not re.search('^[0-9\.]+$', shea_trees, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Shea Trees (row %d)' % (shea_trees, i + 1)
                            return render(request, self.template_name,
                                          {'active': 'system', 'form': form, 'error': data})

                    harvested_quantity = smart_str(row[harvested_quantity_col].value).strip()
                    if harvested_quantity:
                        if not re.search('^[0-9\.]+$', harvested_quantity, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Harvest Quantity (row %d)' % (harvested_quantity, i + 1)
                            return render(request, self.template_name,
                                          {'active': 'system', 'form': form, 'error': data})

                    sunflower_acreage = smart_str(row[sunflower_acreage_col].value).strip()
                    if sunflower_acreage:
                        if not re.search('^[0-9\.]+$', sunflower_acreage, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Sunflower Acreage (row %d)' % (
                            sunflower_acreage, i + 1)
                            return render(request, self.template_name,
                                          {'active': 'system', 'form': form, 'error': data})

                    sunflower_planted = smart_str(row[sunflower_planted_col].value).strip()
                    if sunflower_planted:
                        if not re.search('^[0-9\.]+$', sunflower_planted, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Sunflower Planted (row %d)' % (
                                sunflower_planted, i + 1)
                            return render(request, self.template_name,
                                          {'active': 'system', 'form': form, 'error': data})

                    sunflower_collected = smart_str(row[sunflower_collected_col].value).strip()
                    if sunflower_collected:
                        if not re.search('^[0-9\.]+$', sunflower_collected, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Sunflower Collected (row %d)' % (
                                sunflower_collected, i + 1)
                            return render(request, self.template_name,
                                          {'active': 'system', 'form': form, 'error': data})

                    q = {
                        'farmer_name': farmer_name,
                        'identification': identification,
                        'gender': gender,
                        'date_of_birth': date_of_birth,
                        'phone_number': phone_number,
                        'role': role,
                        'acreage': acreage,
                        # 'soya': soya,
                        # 'soghum': soghum,
                        'cooperative': cooperative,
                        'district': district,
                        'county': county,
                        'sub_county': sub_county,
                        'parish': parish,
                        'village': village,
                        'user_id': user_id,
                        'shea_trees': shea_trees,
                        'harvested_quantity': harvested_quantity,
                        'sunflower_acreage': sunflower_acreage,
                        'sunflower_planted': sunflower_planted,
                        'sunflower_collected': sunflower_collected,
                        'record_id': record_id,
                        'verified_record': verified_record
                    }
                    member_list.append(q)
                
                except Exception as err:
                    log_error()
                    return render(request, self.template_name, {'active': 'setting', 'form':form, 'error': err})
            not_found_records = []
            print(member_list)
            if member_list:
                try:
                    with transaction.atomic():

                        do = None
                        sco = None
                        co = None
                        po = None
                        vo = None
                        count_added = 0
                        count_updated = 0
                        for c in member_list:
                            name = c.get('farmer_name').split(' ')
                            surname = name[0]
                            record_id = c.get('record_id')
                            verified_record = c.get('verified_record')
                            first_name = name[1] if len(name) > 1 else None
                            other_name = name[2] if len(name) > 2 else None
                            identification = c.get('identification')
                            cooperative = c.get('cooperative')
                            district = c.get('district')
                            sub_county = c.get('sub_county')
                            county = c.get('county')
                            parish = c.get('parish')
                            village = c.get('village')
                            user_id = c.get('user_id')

                            shea_trees = int(float(c.get('shea_trees') ))if c.get('shea_trees') != '' else None
                            harvested_quantity = float(c.get('harvested_quantity')) if c.get('harvested_quantity') != '' else None
                            sunflower_acreage = float(c.get('sunflower_acreage')) if c.get('sunflower_acreage') != '' else None
                            sunflower_planted = float(c.get('sunflower_planted')) if c.get('sunflower_planted') != '' else None
                            sunflower_collected = float(c.get('sunflower_collected')) if c.get('sunflower_collected') != '' else None


                            phone_number = c.get('phone_number')
                            acreage = c.get('acreage') if c.get('acreage') != '' else 0
                            # soya = c.get('soya') if c.get('soya') != '' else 0
                            # soghum = c.get('soghum') if c.get('soghum') != '' else 0
                            phone_number = c.get('phone_number')
                            gender = c.get('gender')
                            role = c.get('role')
                            date_of_birth = c.get('date_of_birth') if c.get('date_of_birth') != '' else None
    
                            if district:
                                dl = [dist for dist in District.objects.filter(name__iexact=district)]
                                do = dl[0] if len(dl)>0 else None

                            if county:
                                cl = [c for c in County.objects.filter(name__iexact=county)]
                                co = cl[0] if len(cl)>0 else None
                            
                            if sub_county:
                                scl = [subc for subc in SubCounty.objects.filter(name__iexact=sub_county)]
                                sco = scl[0] if len(scl)>0 else None
                                
                            if parish:
                                pl = [p for p in Parish.objects.filter(name__iexact=parish)]
                                po = pl[0] if len(pl)>0 else None

                            if village:
                                if self.is_numeric(village):
                                    print("Villahge %s " % int(float(village)))
                                    vl = [v for v in Village.objects.filter(id= int(float(village)))]
                                else:
                                    vl = [v for v in Village.objects.filter(name__iexact=village)]
                                vo = vl[0] if len(vl) > 0 else None

                            print("County |%s| SubCounty %s Parish %s Village: %s " % (county, sub_county, parish, village))
                            print("Location %s %s %s %s %s" % (do, co, sco, po, vo))
                            print("ID: %s HQ: %s SA: %s SP: %s SC: %s" % (identification, harvested_quantity,sunflower_acreage,sunflower_planted,sunflower_collected))

                            # check if the object already exists.
                            print("Updating check %s " % record_id)
                            if record_id:
                                try:
                                    member_obj = CooperativeMember.objects.get(id=record_id)
                                    CooperativeMember.objects.filter(id=record_id).update(
                                        cooperative=cooperative,
                                        surname=surname,
                                        first_name=first_name,
                                        other_name=other_name,
                                        # id_number=identification,
                                        gender=gender,
                                        date_of_birth=date_of_birth,
                                        phone_number=phone_number if phone_number != '' else None,
                                        id_number_alt=identification if identification !='' else None,
                                        district=do if do else member_obj.district,
                                        county=co if co else member_obj.county,
                                        sub_county=sco if sco else member_obj.sub_county,
                                        parish=po if po else member_obj.parish,
                                        village=vo.name if vo else member_obj.village,
                                        coop_role=role.title(),
                                        land_acreage=acreage,
                                        verified_record=verified_record,
                                        is_active=True,
                                        user_id=user_id,

                                        shea_trees=shea_trees,
                                        harvested_quantity=harvested_quantity,
                                        sunflower_acreage=sunflower_acreage,
                                        sunflower_planted=sunflower_planted,
                                        sunflower_collected=sunflower_collected
                                    )
                                except ObjectDoesNotExist:
                                    not_found_records.append(record_id)
                            else:
                                if not CooperativeMember.objects.filter(id_number=identification).exists():
                                    if not CooperativeMember.objects.filter(first_name=first_name, surname=surname, phone_number=phone_number, user_id=user_id, village=village).exists():
                                        # if not CooperativeMember.objects.filter(id_number=identification).exists():
                                        member = CooperativeMember.objects.create(
                                            cooperative=cooperative if cooperative != '' else None,
                                            surname=surname,
                                            first_name=first_name,
                                            other_name=other_name,
                                            id_number=identification if identification !='' else None,
                                            gender=gender,
                                            member_id=self.generate_member_id(cooperative),
                                            date_of_birth=date_of_birth,
                                            phone_number=phone_number if phone_number != '' else None,
                                            district=do,
                                            county=co,
                                            sub_county=sco,
                                            parish=po,
                                            village=village,
                                            coop_role=role.title(),
                                            land_acreage=acreage,
                                            # soya_beans_acreage=soya,
                                            # soghum_acreage=soghum,
                                            create_by=request.user,
                                            user_id=user_id,
                                            verified_record=True,
                                            is_active=True,

                                            shea_trees=shea_trees,
                                            harvested_quantity=harvested_quantity,
                                            sunflower_acreage=sunflower_acreage,
                                            sunflower_planted=sunflower_planted,
                                            sunflower_collected=sunflower_collected,

                                        )

                                        message = message_template().member_registration
                                        # if message:
                                        #    if re.search('<NAME>', message):
                                        #        if member.surname:
                                        #            message = message.replace('<NAME>', '%s %s' % (member.surname.title(), member.first_name.title()))
                                        #        message = message.replace('<COOPERATIVE>', member.cooperative.name)
                                        #        message = message.replace('<IDNUMBER>', member.member_id)
                                        #    sendMemberSMS(request, member, message)
                                        count_added += 1
                                else:

                                    CooperativeMember.objects.filter(id_number=identification).update(
                                        is_active=True,
                                        user_id=user_id,
                                        shea_trees=shea_trees,
                                        harvested_quantity=harvested_quantity,
                                        sunflower_acreage=sunflower_acreage,
                                        sunflower_planted=sunflower_planted,
                                        sunflower_collected=sunflower_collected
                                    )
                                    count_added += 1
                        if not_found_records:
                            messages.warning(request, "No records with the following IDs ({}) were found.".format(not_found_records))
                        messages.success(request, "Records aded %s Updated %s" % (count_added, count_updated))
                        return redirect('coop:member_list')
                except Exception as err:
                    log_error()
                    data['error'] = "%s %s" % (err, identification)
                
        data['form'] = form
        return render(request, self.template_name, data)

    def generate_member_id(self, cooperative):
        member = CooperativeMember.objects.all()
        count = member.count() + 1
        today = datetime.today()
        datem = today.year
        yr = str(datem)[2:]
        # idno = generate_numeric(size=4, prefix=str(m.cooperative.code)+yr)
        fint = "%04d"%count
        idno = generate_numeric(4)+yr+fint
        if cooperative:
            idno = str(cooperative.code)+yr+fint
        log_debug("Code is %s" % (idno))
        return idno

    def is_numeric(self, n):
        # return isinstance(n, (int, float))
        try:
            float(n)  # Try converting the string to a float
            return True
        except ValueError:
            return False


class MemberBulkUpdate(ExtraContext, View):
    template_name = 'coop/collection_upload.html'

    def get(self, request, *args, **kwargs):
        data = dict()
        data['form'] = MemberUploadUpdateForm
        return render(request, self.template_name, data)

    def post(self, request, *args, **kwargs):
        data = dict()
        form = MemberUploadUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['excel_file']

            path = f.temporary_file_path()
            index = int(form.cleaned_data['sheet']) - 1
            startrow = int(form.cleaned_data['row']) - 1

            id_col = int(form.cleaned_data['id_col'])
            member_id_col = int(form.cleaned_data['member_id_col'])
            land_acreage_col = int(form.cleaned_data['land_acreage_col'])
            shea_trees_col = int(form.cleaned_data['shea_trees_col'])
            nin_col = int(form.cleaned_data['nin_col'])


            book = xlrd.open_workbook(filename=path, logfile='/tmp/xls.log')
            sheet = book.sheet_by_index(index)
            rownum = 0
            data = dict()
            member_list = []
            for i in range(startrow, sheet.nrows):
                try:
                    row = sheet.row(i)
                    rownum = i + 1

                    sys_id = smart_str(row[id_col].value).strip()
                    member_id = smart_str(row[member_id_col].value).strip()
                    land_acreage = smart_str(row[land_acreage_col].value).strip()
                    shea_trees = smart_str(row[shea_trees_col].value).strip()
                    nin = smart_str(row[nin_col].value).strip()

                    member = CooperativeMember.objects.get(pk=sys_id, member_id=member_id)


                    q = {
                        'farmer_name': farmer_name,
                        'identification': identification,
                        'gender': gender,
                        'date_of_birth': date_of_birth,
                        'phone_number': phone_number,
                        'role': role,
                        'acreage': acreage,
                        # 'soya': soya,
                        # 'soghum': soghum,
                        'cooperative': cooperative,
                        'district': district,
                        'county': county,
                        'sub_county': sub_county,
                        'parish': parish,
                        'village': village
                    }
                    member_list.append(q)

                except Exception as err:
                    log_error()
                    return render(request, self.template_name, {'active': 'setting', 'form': form, 'error': err})
            print(member_list)
            if member_list:
                with transaction.atomic():
                    try:
                        do = None
                        sco = None
                        co = None
                        po = None
                        for c in member_list:
                            name = c.get('farmer_name').split(' ')
                            surname = name[0]
                            first_name = name[1] if len(name) > 1 else None
                            other_name = name[2] if len(name) > 2 else None
                            identification = c.get('identification')
                            cooperative = c.get('cooperative')
                            district = c.get('district')
                            sub_county = c.get('sub_county')
                            county = c.get('county')
                            parish = c.get('parish')
                            village = c.get('village')
                            phone_number = c.get('phone_number')
                            acreage = c.get('acreage') if c.get('acreage') != '' else 0
                            # soya = c.get('soya') if c.get('soya') != '' else 0
                            # soghum = c.get('soghum') if c.get('soghum') != '' else 0
                            phone_number = c.get('phone_number')
                            gender = c.get('gender')
                            role = c.get('role')
                            date_of_birth = c.get('date_of_birth') if c.get('date_of_birth') != '' else None

                            if district:
                                dl = [dist for dist in District.objects.filter(name__iexact=district)]
                                do = dl[0] if len(dl) > 0 else None

                            if county:
                                cl = [c for c in County.objects.filter(district__name=district, name=county)]
                                co = cl[0] if len(cl) > 0 else None

                            if sub_county:
                                scl = [subc for subc in SubCounty.objects.filter(county__name=county, name=sub_county)]
                                sco = scl[0] if len(scl) > 0 else None

                            if parish:
                                pl = [p for p in Parish.objects.filter(sub_county__name=sub_county, name=parish)]
                                po = pl[0] if len(pl) > 0 else None

                            if not CooperativeMember.objects.filter(first_name=first_name, surname=surname,
                                                                    phone_number=phone_number).exists():
                                member = CooperativeMember.objects.create(
                                    cooperative=cooperative,
                                    surname=surname,
                                    first_name=first_name,
                                    other_name=other_name,
                                    id_number=identification,
                                    gender=gender,
                                    member_id=self.generate_member_id(cooperative),
                                    date_of_birth=date_of_birth,
                                    phone_number=phone_number if phone_number != '' else None,
                                    district=do,
                                    county=co,
                                    sub_county=sco,
                                    parish=po,
                                    village=village,
                                    coop_role=role.title(),
                                    land_acreage=acreage,
                                    # soya_beans_acreage = soya,
                                    # soghum_acreage = soghum,
                                    create_by=request.user
                                )

                                message = message_template().member_registration
                                # if message:
                                #    if re.search('<NAME>', message):
                                #        if member.surname:
                                #            message = message.replace('<NAME>', '%s %s' % (member.surname.title(), member.first_name.title()))
                                #        message = message.replace('<COOPERATIVE>', member.cooperative.name)
                                #        message = message.replace('<IDNUMBER>', member.member_id)
                                #    sendMemberSMS(request, member, message)

                        return redirect('coop:member_list')
                    except Exception as err:
                        log_error()
                        data['error'] = err

        data['form'] = form
        return render(request, self.template_name, data)

    def generate_member_id(self, cooperative):
        member = CooperativeMember.objects.all()
        count = member.count() + 1
        today = datetime.today()
        datem = today.year
        yr = str(datem)[2:]
        # idno = generate_numeric(size=4, prefix=str(m.cooperative.code)+yr)
        fint = "%04d" % count
        idno = str(cooperative.code) + yr + fint
        log_debug("Cooperative %s code is %s" % (cooperative.code, idno))
        return idno


class CooperativeMemberListView(ExtraContext, ListView):
    model = CooperativeMember
    template_name = 'coop/cooperativemember_list.html'
    ordering = ['-id']
    
    def dispatch(self, *args, **kwargs):
        if self.request.GET.get('download'):
            return self.download_file(*args, **kwargs)
        if self.request.GET.get('csv'):
            return self.download_csv(*args, **kwargs)
        return super(CooperativeMemberListView, self).dispatch(*args, **kwargs)
    
    def get_queryset(self):
        queryset = super(CooperativeMemberListView, self).get_queryset()
        search = self.request.GET.get('search')
        msisdn = self.request.GET.get('phone_number')
        name = self.request.GET.get('name')
        coop = self.request.GET.get('cooperative')
        role = self.request.GET.get('role')
        district = self.request.GET.get('district')
        create_by = self.request.GET.get('create_by')
        verified = self.request.GET.get('verified')
        end_date = self.request.GET.get('end_date')
        start_date = self.request.GET.get('start_date')
        start_time = self.request.GET.get('start_time') if self.request.GET.get('start_time') else "00:00"
        end_time = self.request.GET.get('end_time') if self.request.GET.get('end_time') else "23:59"
        filter_start_date = "%s %s" % (start_date, start_time)
        filter_end_time = "%s %s" % (end_date, end_time)

        if not self.request.user.profile.is_union():
            cooperative = self.request.user.cooperative_admin.cooperative 
            queryset = queryset.filter(cooperative=cooperative)

        queryset = queryset.filter(is_active=True)

        if search:
            queryset = queryset.filter(Q(surname__icontains=search) | Q(first_name__icontains=search) | Q(id__icontains=search)|
                                       Q(id_number__icontains=search)|Q(user_id__icontains=search))
        if msisdn:
            queryset = queryset.filter(phone_number__icontains='%s' % msisdn)
        if name:
            #name=Concat('surname',V(' '),'first_name',V(' '),'other_name')
            queryset = queryset.filter(Q(surname__icontains=name)|Q(first_name__icontains=name)|Q(other_name=name))
            #queryset = queryset.filter(Concat(surname,V(' '),first_name,V(' '),other_name)=name)
        if coop:
            queryset = queryset.filter(cooperative__id=coop)
        if role:
            queryset = queryset.filter(coop_role=role)
        if verified:
            queryset = queryset.filter(verified_record=True)
        if district:
            queryset = queryset.filter(district__id=district)
        if create_by:
            queryset = queryset.filter(create_by__profile__id=create_by)
        if start_date:
            queryset = queryset.filter(create_date__gte=filter_start_date)
        if end_date:
            queryset = queryset.filter(create_date__lte=filter_end_time)
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super(CooperativeMemberListView, self).get_context_data(**kwargs)
        context['form'] = MemberProfileSearchForm(self.request.GET, request=self.request)
        qr = self.get_queryset()
        of = qr.filter(own_phone=True)
        hmm = qr.filter(has_mobile_money=True)
        context['own_phone'] = of.count()
        context['has_mobile_money'] = hmm.count()
        return context
    
    def download_file(self, *args, **kwargs):
        _value = []
        columns = []
        msisdn = self.request.GET.get('phone_number')
        name = self.request.GET.get('name')
        coop = self.request.GET.get('cooperative')
        role = self.request.GET.get('role')
        verified = self.request.GET.get('verified')
        district = self.request.GET.get('district')
        create_by = self.request.GET.get('create_by')
        end_date = self.request.GET.get('end_date')
        start_date = self.request.GET.get('start_date')
        start_time = self.request.GET.get('start_time') if self.request.GET.get('start_time') else "00:00"
        end_time = self.request.GET.get('end_time') if self.request.GET.get('end_time') else "23:59"
        filter_start_date = "%s %s" % (start_date, start_time)
        filter_end_time = "%s %s" % (end_date, end_time)

        profile_choices = ['id', 'user_id', 'cooperative__name', 'farmer_group__name', 'member_id', 'surname', 'first_name', 'other_name',
                               'date_of_birth', 'gender', 'id_number','phone_number','email',
                               'district__name', 'county__name', 'sub_county__name', 'parish__name', 'village','address','gps_coodinates',
                               'coop_role','land_acreage', 'shea_trees', 'bee_hives', 'product',
                               'collection_amount','collection_quantity', 'paid_amount', 'create_by__username',
                                'harvested_quantity', 'sunflower_acreage', 'sunflower_planted', 'sunflower_collected', 'app_id', 'create_date']

        columns += [self.replaceMultiple(c, ['_', '__name'], ' ').title() for c in profile_choices]
        # Gather the Information Found
        # Create the HttpResponse object with Excel header.This tells browsers that 
        # the document is a Excel file.
        response = HttpResponse(content_type='application/ms-excel')
        
        # The response also has additional Content-Disposition header, which contains 
        # the name of the Excel file.
        response['Content-Disposition'] = 'attachment; filename=CooperativeMembers_%s.xls' % datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Create object for the Workbook which is under xlwt library.
        workbook = xlwt.Workbook()
        
        # By using Workbook object, add the sheet with the name of your choice.
        worksheet = workbook.add_sheet("Members")

        row_num = 0
        style_string = "font: bold on; borders: bottom dashed"
        style = xlwt.easyxf(style_string)

        for col_num in range(len(columns)):
            # For each cell in your Excel Sheet, call write function by passing row number, 
            # column number and cell data.
            worksheet.write(row_num, col_num, columns[col_num], style=style)

        _members = CooperativeMember.objects.values(*profile_choices).all()
        _members = _members.filter(is_active=True)
        
        if msisdn:
            _members = _members.filter(phone_number='%s' % msisdn)
        if name:
            _members = _members.filter(Q(surname__icontains=name)|Q(first_name__icontains=name)|Q(other_name=name))
        if coop:
            _members = _members.filter(cooperative__id=coop)
        if role:
            _members = _members.filter(coop_role=role)
        if verified:
            _members = _members.filter(verified_record=True)
        if district:
            _members = _members.filter(district__id=district)
        if create_by:
            _members = _members.filter(create_by__profile__id=create_by)
        if start_date:
            _members = _members.filter(create_date__gte=filter_start_date)
        if end_date:
            _members = _members.filter(create_date__lte=filter_end_time)
        
        for m in _members:
            row_num += 1
            # ##print profile_choices
            row = [m['%s' % x] if 'create_date' not in x else m['%s' % x].strftime('%d-%m-%Y %H:%M:%S') if 'date_of_birth' not in x else m['%s' % x].strftime('%d-%m-%Y') if m.get('%s' % x) else ""  for x in profile_choices]
            
            for col_num in range(len(row)):
                worksheet.write(row_num, col_num, row[col_num])
        workbook.save(response)
        return response

    def download_csv(self, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="CooperativeMembers_%s.csv"' % datetime.now().strftime('%Y%m%d%H%M%S')

        writer = csv.writer(response)
        _value = []
        columns = []
        print(self.request)
        msisdn = self.request.GET.get('phone_number')
        name = self.request.GET.get('name')
        coop = self.request.GET.get('cooperative')
        role = self.request.GET.get('role')
        district = self.request.GET.get('district')
        create_by = self.request.GET.get('create_by')
        end_date = self.request.GET.get('end_date')
        start_date = self.request.GET.get('start_date')
        start_time = self.request.GET.get('start_time') if self.request.GET.get('start_time') else "00:00"
        end_time = self.request.GET.get('end_time') if self.request.GET.get('end_time') else "23:59"
        filter_start_date = "%s %s" % (start_date, start_time)
        filter_end_time = "%s %s" % (end_date, end_time)

        profile_choices = ['id', 'user_id', 'cooperative__name', 'farmer_group__name', 'member_id', 'surname', 'first_name',
                           'other_name',
                           'date_of_birth', 'gender', 'id_number', 'phone_number', 'email',
                           'district__name', 'county__name', 'sub_county__name', 'parish__name', 'village', 'address',
                           'gps_coodinates',
                           'coop_role', 'land_acreage', 'shea_trees', 'bee_hives', 'product',
                           'collection_amount', 'collection_quantity', 'paid_amount', 'create_by__username',
                           'harvested_quantity', 'sunflower_acreage', 'sunflower_planted', 'sunflower_collected',
                           'create_date']

        columns += [self.replaceMultiple(c, ['_', '__name'], ' ').title() for c in profile_choices]

        # for col_num in range(len(columns)):
        #     # For each cell in your Excel Sheet, call write function by passing row number,
        #     # column number and cell data.
        #     worksheet.write(row_num, col_num, columns[col_num], style=style)
        writer.writerow(columns)  # Add column headers

        _members = CooperativeMember.objects.values(*profile_choices).all()  # Modify the queryset based on your needs
        _members = _members.filter(is_active=True)

        if msisdn:
            _members = _members.filter(phone_number='%s' % msisdn)
        if name:
            _members = _members.filter(Q(surname__icontains=name)|Q(first_name__icontains=name)|Q(other_name=name))
        if coop:
            _members = _members.filter(cooperative__id=coop)
        if role:
            _members = _members.filter(coop_role=role)
        if district:
            _members = _members.filter(district__id=district)
        if create_by:
            print("teed")
            _members = _members.filter(create_by__profile__id=create_by)
        if start_date:
            _members = _members.filter(create_date__gte=filter_start_date)
        if end_date:
            _members = _members.filter(create_date__lte=filter_end_time)

        for m in _members:
            row = [m['%s' % x] if 'create_date' not in x else m['%s' % x].strftime(
                '%d-%m-%Y %H:%M:%S') if 'date_of_birth' not in x else m['%s' % x].strftime('%d-%m-%Y') if m.get(
                '%s' % x) else "" for x in profile_choices]
            writer.writerow(row)  # Add object data

        return response
    
    def replaceMultiple(self, mainString, toBeReplaces, newString):
        # Iterate over the strings to be replaced
        for elem in toBeReplaces :
            # Check if string is in the main string
            if elem in mainString :
                # Replace the string
                mainString = mainString.replace(elem, newString)
        
        return mainString


class ImageQRCodeDownloadView(View):
    def get(self, request, *args, **kwargs):
        try:
            pk = self.kwargs.get('pk')
            qs = CooperativeMember.objects.get(pk=pk)
            image = qs.get_qrcode()
            # print image.path
            image_buffer = open(image.path, "rb").read()
            content_type = magic.from_buffer(image_buffer, mime=True)
            response = HttpResponse(image_buffer, content_type=content_type);
            response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(image.path)
            return response
        except Exception:
            log_error()
            return redirect('coop:member_list') 


class DeprecatedDownloadExcelMemberView(View):
    template_name = 'coop/download_member.html'
    
    def get(self, request, *args, **kwargs):
        form = DownloadMemberOptionForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = DownloadMemberOptionForm(request.POST)
        if form.is_valid():
            _value = []
            profile = form.cleaned_data.get('profile')
            # farm = form.cleaned_data.get('farm')
            # deworming = form.cleaned_data.get('deworming')
            # breed = form.cleaned_data.get('breed')
            # bull_herd = form.cleaned_data.get('bull_herd')
            # cow_herd = form.cleaned_data.get('cow_herd')
            # member_supply = form.cleaned_data.get('member_supply')
            _value += profile
            # _value+= farm
            # _value += deworming
            # _value += breed
            # _value += bull_herd
            # _value += cow_herd
            # _value += member_supply
            if len(profile) > 0:
                _members = CooperativeMember.objects.values(*[x for x in profile]).all()
                for m in _members:
                    if len(farm) > 0:
                        _biz = CooperativeMemberBusiness.objects.values(*[x for x in farm]).filter(cooperative_member=m)
                    if len(deworming) > 0:
                        _deworm = DewormingSchedule.objects.values(*[x for x in deworming]).filter(cooperative_member=m)
                    if len(breed) > 0:
                        _breeds = CooperativeMemberProductDefinition.objects.values(*[x for x in deworming]).filter(cooperative_member=m)
                    if len(bull_herd) > 0:
                        _bulls = CooperativeMemberHerdMale.objects.values(*[x for x in bull_herd]).filter(cooperative_member=m)
                    if len(cow_herd) > 0:
                        _cows = CooperativeMemberHerdFemale.objects.values(*[x for x in cow_herd]).filter(cooperative_member=m)
                    if len(member_supply) > 0:
                        deworm = CooperativeMemberSupply.objects.values(*[x for x in member_supply]).filter(cooperative_member=m)
                
            raise Exception(len(farm))
        return render(request, self.template_name, {'form': form})


class DownloadExcelMemberView(View):
    template_name = 'coop/download_member.html'
    
    def get(self, request, *args, **kwargs):
        form = DownloadMemberOptionForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = DownloadMemberOptionForm(request.POST)
        if form.is_valid():
            _value = []
            profile = form.cleaned_data.get('profile')
            farm = form.cleaned_data.get('farm')
            herd = form.cleaned_data.get('herd')
            member_supply = form.cleaned_data.get('member_supply')
            columns = []
            
            profile_choices = ['id','cooperative__name', 'member_id', 'surname', 'first_name', 'other_name',
                               'date_of_birth', 'gender', 'maritual_status','phone_number','email',
                               'district__name','sub_county__name','village','address','gps_coodinates',
                               'coop_role','cotton_acreage', 'soya_beans_acreage','soghum_acreage','shares',
                               'collection_amount','collection_quantity', 'paid_amount']
            
            farm_choices = ['business_name', 'farm_district__name','farm_sub_county__name', 'gps_coodinates',
                            'size', 'fenced', 'paddock','water_source',
                            'animal_identification','common_diseases','other_animal_diseases','tick_control']
    
            male_herd = ['adults', 'bullocks', 'calves']
            female_herd = ['f_adults', 'heifers', 'f_calves']
            member_supply_choice = ['nearest_market','product_average_cost','price_per_kilo','probable_sell_month',
                              'probable_sell_month', 'sell_to_cooperative_society']
            
            columns += [self.replaceMultiple(c, ['_', '__name'], ' ').title() for c in profile_choices]
            if farm:
                columns += [self.replaceMultiple(c, ['_', '__name'], ' ').title() for c in farm_choices]
                columns += ['Deworm Schedule']
            if herd:
                columns += ['Breeds']
                columns += [self.replaceMultiple(c, ['_', '__name'], ' ').title() for c in male_herd]
                columns += [self.replaceMultiple(c, ['_', '__name'], ' ').title() for c in female_herd]
            if member_supply:
                columns += [self.replaceMultiple(c, ['_', '__name'], ' ').title() for c in member_supply_choice]
            #Gather the Information Found
            # Create the HttpResponse object with Excel header.This tells browsers that 
            # the document is a Excel file.
            response = HttpResponse(content_type='application/ms-excel')
            
            # The response also has additional Content-Disposition header, which contains 
            # the name of the Excel file.
            response['Content-Disposition'] = 'attachment; filename=CooperativeMembers_%s.xls' % datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Create object for the Workbook which is under xlwt library.
            workbook = xlwt.Workbook()
            
            # By using Workbook object, add the sheet with the name of your choice.
            worksheet = workbook.add_sheet("Members")

            row_num = 0
            style_string = "font: bold on; borders: bottom dashed"
            style = xlwt.easyxf(style_string)

            for col_num in range(len(columns)):
                # For each cell in your Excel Sheet, call write function by passing row number, 
                # column number and cell data.
                worksheet.write(row_num, col_num, columns[col_num], style=style)
            
            if profile:
                _members = CooperativeMember.objects.values(*profile_choices).all()
                
                for m in _members:
                    
                    if farm:
                        _biz = CooperativeMemberBusiness.objects.values(*farm_choices).filter(cooperative_member=m['id'])
                        _deworm = DewormingSchedule.objects.values('deworm_date','dewormer').filter(cooperative_member=m['id'])
                    if herd:
                        _breeds = CooperativeMemberProductDefinition.objects.filter(cooperative_member=m['id'])
                        _bulls = CooperativeMemberHerdMale.objects.values(*male_herd).filter(cooperative_member=m['id'])
                        _cows = CooperativeMemberHerdFemale.objects.values(*female_herd).filter(cooperative_member=m['id'])
                    if member_supply:
                        _member_supply = CooperativeMemberSupply.objects.values(*member_supply_choice).filter(cooperative_member=m['id'])
                    
                    row_num += 1
                    row = [m['%s' % x] for x in profile_choices]
                    if farm:
                        if _biz.exists():
                            row += [_biz[0]['%s' % x] for x in farm_choices]
                        if _deworm.exists():
                            row += [','.join(['%s | %s' % (dw['deworm_date'], dw['dewormer']) for dw in _deworm])]
                    if herd:
                        if _breeds.exists():
                            row += ['|'.join([brd.name for brd in _breeds[0].product_variation.all()])]
                        if _bulls.exists():
                            row += [_bulls[0]['%s' % x] for x in male_herd]
                        if _cows.exists():
                            row += [_cows[0]['%s' % x] for x in female_herd]
                    if member_supply:
                        if _member_supply.exists():
                            row += [_member_supply[0]['%s' % x] for x in member_supply_choice]
                    for col_num in range(len(row)):
                        worksheet.write(row_num, col_num, row[col_num])
                workbook.save(response)
                return response
                                        
            
        return render(request, self.template_name, {'form': form})

    def replaceMultiple(self, mainString, toBeReplaces, newString):
        # Iterate over the strings to be replaced
        for elem in toBeReplaces :
            # Check if string is in the main string
            if elem in mainString :
                # Replace the string
                mainString = mainString.replace(elem, newString)
        
        return  mainString


class SendCommunicationView(View):
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SendCommunicationView, self).dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        msisdn = self.request.GET.get('phone_number')
        name = self.request.GET.get('name')
        coop = self.request.GET.get('cooperative')
        role = self.request.GET.get('role')
        district = self.request.GET.get('district')
        jres = {'status': 'error', 'message': 'Unknown Error! Message not sent. Contact Admin.'}
        try:
            queryset =  CooperativeMember.objects.all()
            if not request.user.profile.is_union():
                queryset = queryset.filter(cooperative = request.user.cooperative_admin.cooperative)
            response = ""
            if msisdn:
                queryset = queryset.filter(phone_number='%s' % msisdn)
                response += "Phone Number " + msisdn
            if name:
                queryset = queryset.filter(Q(surname__icontains=name)|Q(first_name__icontains=name)|Q(other_name=name))
                response += " Name "
            if coop:
                queryset = queryset.filter(cooperative__id=coop)
                c = Cooperative.objects.get(pk=coop)
                response += " Cooperative "+c.name
            if role:
                queryset = queryset.filter(coop_role=role)
                response += " Role " + role
            if district:
                queryset = queryset.filter(district__id=district)
                d = District.objects.get(pk=district)
                response += " District " + d.name    
            response += "<div>Total Messages %s</div>" % queryset.count()
            jres = {'status': 'success', 'message': response}
        except Exception:
            log_error()
            jres = {'status': 'error', 'message': 'Error! Messages not Sent.'}
            
        return JsonResponse(jres)
    
    def post(self, request,  *args, **kwargs):
        ##print " Message: %s" % (self.request.body)
        body_unicode = self.request.body.decode('utf-8')
        data = json.loads(body_unicode)
        
        msisdn = data.get('phone_number')
        name = data.get('name')
        coop = data.get('cooperative')
        role = data.get('role')
        district = data.get('district')
        jres = {'status': 'error', 'message': 'Unknown Error! Message not sent. Contact Admin.'}
        
        try:
            queryset =  CooperativeMember.objects.all()
            if not request.user.profile.is_union():
                queryset = queryset.filter(cooperative = request.user.cooperative_admin.cooperative)
            if msisdn:
                queryset = queryset.filter(phone_number='%s' % msisdn)
            if name:
                queryset = queryset.filter(Q(surname__icontains=name)|Q(first_name__icontains=name)|Q(other_name=name))
            if coop:
                queryset = queryset.filter(cooperative__id=coop)
            if role:
                queryset = queryset.filter(coop_role=role)
            if district:
                queryset = queryset.filter(district__id=district)
            
            for q in queryset:
                count = 0
                message = data.get('message')
                msisdn = q.phone_number
                if re.search('<NAME>', message):
                    if q.surname:
                        message = message.replace('<NAME>', q.surname.title())
                #print "%s Message: %s" % (q.phone_number, message)
                sms = sendMemberSMS(self.request, q, message)
                if sms:
                    count += 1
            jres = {'status': 'success', 'message': '%s Messages sent. <div><small>If some messages were not sent, Please check the send Message status of the Cooperative</small</div>' % count}
        except Exception:
            log_error()
            jres = {'status': 'error', 'message': 'Error! Message not sent. Contact Admin.'}
        return JsonResponse(jres)
    
    
class CooperativeMemberDetailView(ExtraContext, DetailView):
    model = CooperativeMember
    
    def get_queryset(self):
        qs = super(CooperativeMemberDetailView, self). get_queryset()
        if not self.request.user.profile.is_union():
            cooperative = self.request.user.cooperative_admin.cooperative 
            qs = qs.filter(cooperative=cooperative) 
        return qs
    
    def get_context_data(self, **kwargs):
        context = super(CooperativeMemberDetailView, self).get_context_data(**kwargs)
        context['training'] = TrainingAttendance.objects.filter(coop_member__id=self.kwargs.get('pk'))
        #raise Exception(context['training'])
        return context
    

class MemberSubscriptionListView(ExtraContext, ListView):
    model = CooperativeMemberSubscriptionLog
    

class MemberSubscriptionCreateView(ExtraContext, CreateView):
    model = CooperativeMemberSubscriptionLog
    form_class = MemberSubscriptionForm
    success_url = reverse_lazy('coop:member_subscription_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.transaction_id = generate_alpanumeric()
        bal_before = form.instance.cooperative_member.subscription_amount
        bal_after = bal_before + form.instance.amount_paid
        form.instance.cooperative_member.subscription_amount = bal_after
        form.instance.cooperative_member.save()
        # form.instance.new_balance = bal_after
        return super(MemberSubscriptionCreateView, self).form_valid(form)
    
    
class MemberSubscriptionUpdateView(ExtraContext, UpdateView):
    model = CooperativeMemberSubscriptionLog
    form_class = MemberSubscriptionForm
    success_url = reverse_lazy('coop:member_subscription_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        cont = CooperativeMemberSubscriptionLog.objects.get(pk=form.instance.id)
        acc_bal = form.instance.cooperative_member.subscription_amount
        deducted = acc_bal - cont.amount_paid
        final = deducted + form.instance.amount_paid
        form.instance.cooperative_member.subscription_amount = final
        form.instance.cooperative_member.save()
        # form.instance.new_balance = final
        return super(MemberSubscriptionUpdateView, self).form_valid(form)


class MemberSharesView(ListView):
    model = CooperativeMemberSharesLog
    template_name = 'coop/MemberShares.html'
    
    def get_queryset(self):
        queryset = CooperativeMemberSharesLog.objects
        if not self.request.user.profile.is_union():
            cooperative = self.request.user.cooperative_admin.cooperative 
            queryset = queryset.filter(cooperative_member__cooperative = cooperative)
        queryset = queryset.values('cooperative_member',
                                   name=Concat('cooperative_member__surname',
                                               V(' '),
                                               'cooperative_member__first_name'
                                               ),
                                   
                                   ).annotate(total_amount=Sum('amount'), total_shares=Sum('shares'), transaction_date=Max('transaction_date')).order_by('-transaction_date')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super(MemberSharesView, self).get_context_data(**kwargs)
        context['active'] = ['_coop_member_shares']
        return context


# Registrton
class MemberRegistrationTransactionListView(ExtraContext, ListView):
    model = RegistrationTransaction
    template_name = 'coop/memberregistrationlist.html'

    def get_queryset(self):
        queryset = RegistrationTransaction.objects.all()
        if not self.request.user.profile.is_union():
            cooperative = self.request.user.cooperative_admin.cooperative
            queryset = queryset.filter(member__cooperative=cooperative)
        member = self.kwargs.get('member')
        if member:
            queryset = queryset.filter(member=member)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(MemberRegistrationTransactionListView, self).get_context_data(**kwargs)
        context['active'] = ['_coop_reg_shares']
        return context


class MemberRegistrationTransactionCreateView(FormView):
    # model = RegistrationTransaction
    form_class = RegistrationTransactionForm
    success_url = reverse_lazy('coop:registration_list')
    template_name = "coop/registrationtransaction_form.html"

    def get_form_kwargs(self, **kwargs):
        kwargs = super(MemberRegistrationTransactionCreateView, self).get_form_kwargs(**kwargs)
        kwargs['request'] = self.request  # pass the 'user' in kwargs
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        transaction_id = generate_alpanumeric()
        msisdn = form.cleaned_data.get('phone_number')
        member = form.cleaned_data.get('member')
        amount = form.cleaned_data.get('amount')

        registration = RegistrationTransaction.objects.filter(member=member)
        if registration.exists():
            return JsonResponse({"error": True, "response": "This member is arleady registered."})

        try:
            msisdn = internationalize_number(msisdn)
        except Exceptoin as e:
            return JsonResponse({"error": True, "response": "Phone Number provided is invalid."})

        account = member.cooperative.account

        try:
            transaction = AccountTransaction.objects.create(
                account=account,
                reference = genetate_uuid4(),
                amount = amount,
                phone_number = msisdn,
                transaction_type = 'COLLECTION',
                entry_type = 'CREDIT',
                category = 'REGISTRATION',
                status = 'PENDING',
                description = 'REGISTRATION FEE for %s' % member,
                request = '',
                request_date = datetime.now(),
                created_by = self.request.user
            )

            credentials = {
                'password': 'W3E4g8weR5TgH0Td2344',
                'accountid': 'andrew',
                'http_credentials': 'andrew:hamwe'
            }
            hamwepay = HamwePay(credentials)

            payload = {
                "reference": transaction.reference,
                "method": 'COLLECTION',
                "amount": "%s" % transaction.amount,
                "phone_number": transaction.phone_number,
            }
            response = hamwepay.mobile_money_transaction(payload)
            status_checking = None
            if response:
                transaction.response = response
                transaction.response_date = datetime.now()
                transaction.save()
                if response.get("transactionStatus") == 'PENDING':
                    status_checking = response
                    reference = response.get('transactionReference')
                    loop = 1
                    while loop == 1:
                        time.sleep(2)
                        log_debug("Check Status")
                        status_checking = hamwepay.check_status(reference)
                        if not status_checking:
                            loop = 0
                        if status_checking.get('status') == 'ERROR':
                            loop = 0
                        if status_checking.get('status') == 'OK':
                            if status_checking.get('statusMessage') != "PENDING":
                                loop = 0
                        else:
                            loop = 0
                log_debug("End Check Status %s" % status_checking)
                if status_checking.get('statusMessage') != "PENDING":
                    transaction.response = status_checking
                    transaction.status = status_checking.get('statusMessage')
                    transaction.response_date = datetime.now()
                    transaction.payment_date = datetime.now()

                    if status_checking.get('statusMessage') == "SUCCESSFUL":

                        balance = account.balance
                        new_balance = balance + amount
                        account.balance = new_balance
                        account.save()

                        transaction.balance_after = new_balance

                        RegistrationTransaction.objects.create(
                            transaction_id=transaction.reference,
                            member = member,
                            amount = transaction.amount,
                            payment_date = datetime.now()
                        )
                        return JsonResponse({"error": False, "response": "Transaction Successful"})
                    elif status_checking.get('statusMessage') == "FAILED":
                        return JsonResponse({"error": True, "response": "Transaction Failed Failed"})
                    else:
                        return JsonResponse({"error": True, "response": "Unknown Status. Contact Admin"})
                transaction.save()

            print(response)

            # try:
            #     message = message_template().member_share_purchase
            #     message = message.replace('<NAME>', member.surname)
            #     message = message.replace('<SHARES>', '%s' % form.instance.shares)
            #     message = message.replace('<AMOUNT>', '%s' % form.instance.amount)
            #     message = message.replace('<TOTAL>', '%s' % bal_after)
            #     message = message.replace('<REFERENCE>', form.instance.transaction_id)
            #     sendMemberSMS(self.request, member, message)
            # except Exception:
            #     log_error()
            # return super(MemberRegistrationTransactionCreateView, self).form_valid(form)
        except Exception as e:
            log_error()
            return JsonResponse({"error": True, "response": "Transaction Failed. Contact Admin"})
        return JsonResponse({"error": False, "response": "Error"})


class MemberSharesUpdateView(UpdateView):
    model = CooperativeMemberSharesLog
    form_class = MemberSharesForm
    success_url = reverse_lazy('coop:member_shares_list')

    def get_form_kwargs(self):
        kwargs = super(MemberSharesUpdateView, self).get_form_kwargs()
        kwargs['request'] = self.request  # pass the 'user' in kwargs
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        cont = CooperativeMemberSharesLog.objects.get(pk=form.instance.id)
        acc_bal = form.instance.cooperative_member.shares
        deducted = acc_bal - cont.shares
        final = deducted + form.instance.shares
        form.instance.cooperative_member.shares = final
        form.instance.cooperative_member.save()
        form.instance.new_shares = final
        return super(MemberSharesUpdateView, self).form_valid(form)
# /Registration

class MemberSharesListView(ExtraContext, ListView):
    model = CooperativeMemberSharesLog
    template_name = 'coop/cooperativemembersharelog_list.html'
    
    def get_queryset(self):
        queryset = CooperativeMemberSharesLog.objects.all()
        if not self.request.user.profile.is_union():
            cooperative = self.request.user.cooperative_admin.cooperative 
            queryset = queryset.filter(cooperative_member__cooperative=cooperative)
        member = self.kwargs.get('member')
        if member:
            queryset = queryset.filter(cooperative_member=member)
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super(MemberSharesListView, self).get_context_data(**kwargs)
        context['active'] = ['_coop_member_shares']
        return context
    

class MemberSharesCreateView(CreateView):
    model = CooperativeMemberSharesLog
    form_class = MemberSharesForm
    success_url = reverse_lazy('coop:member_shares_list')
    
    def get_form_kwargs(self):
        kwargs = super(MemberSharesCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request # pass the 'user' in kwargs
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.transaction_id = generate_alpanumeric()
        bal_before = form.instance.cooperative_member.shares
        amt_before = form.instance.cooperative_member.share_amount
        bal_after = bal_before + form.instance.shares
        amt_after = amt_before + form.instance.amount
        form.instance.cooperative_member.shares = bal_after
        form.instance.cooperative_member.share_amount = amt_after
        form.instance.cooperative_member.save()
        form.instance.new_shares = bal_after
        member = form.instance.cooperative_member
        try:
            message = message_template().member_share_purchase
            message = message.replace('<NAME>', member.surname)
            message = message.replace('<SHARES>', '%s' % form.instance.shares)
            message = message.replace('<AMOUNT>', '%s' % form.instance.amount)
            message = message.replace('<TOTAL>', '%s' %  bal_after)
            message = message.replace('<REFERENCE>', form.instance.transaction_id)
            sendMemberSMS(self.request, member, message)
        except Exception:
            log_error()
        return super(MemberSharesCreateView, self).form_valid(form)
    
    
class MemberSharesUpdateView(UpdateView):
    model = CooperativeMemberSharesLog
    form_class = MemberSharesForm
    success_url = reverse_lazy('coop:member_shares_list')
    
    def get_form_kwargs(self):
        kwargs = super(MemberSharesUpdateView, self).get_form_kwargs()
        kwargs['request'] = self.request # pass the 'user' in kwargs
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        cont = CooperativeMemberSharesLog.objects.get(pk=form.instance.id)
        acc_bal = form.instance.cooperative_member.shares
        deducted = acc_bal - cont.shares
        final = deducted + form.instance.shares
        form.instance.cooperative_member.shares = final
        form.instance.cooperative_member.save()
        form.instance.new_shares = final
        return super(MemberSharesUpdateView, self).form_valid(form)
    

class MemberSupplyRequestListView(ListView):
    model = MemberSupplyRequest
    ordering = ['-create_date']
    
    def get_queryset(self):
        queryset = super(MemberSupplyRequestListView, self).get_queryset()
        
        if not self.request.user.profile.is_union():
            if not self.request.user.profile.is_partner():
                cooperative = self.request.user.cooperative_admin.cooperative 
                queryset = queryset.filter(cooperative_member__cooperative=cooperative)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super(MemberSupplyRequestListView, self).get_context_data(**kwargs)
        context['active'] = ['_coop_supply_request', '']
        return context
    
    
class MemberSupplyRequestCreateView(View):
    
    template_name = 'coop/membersupplyrequest_form.html'
    
    def get(self, request, *args, **kwargs):
        initial = None
        supply = None
        extra = 1
        pk = self.kwargs.get('pk')
        if pk:
            supply = MemberSupplyRequest.objects.get(pk=pk)
            pvars = MemberSupplyRequestVariation.objects.filter(supply_request=supply)
            initial = [{'breed': x.breed, 'total': x.total} for x in pvars]
            extra = 0 if len(initial) > 0 else 1
        
        form = MemberSupplyRequestForm(instance=supply, request=request)
        
        variation_formset = formset_factory(MemberSupplyRequestVariationForm, formset=VariationSupplyRequestFormSet, extra=extra)
        variation_form = variation_formset(prefix='variation', initial=initial)
        return render(request, self.template_name, {'form': form, 'variation_form': variation_form, 'active': ['_coop_supply_request', '']})
    
    def post(self, request, *args, **kwargs):
        initial = None
        supply = None
        extra = 1
        pk = self.kwargs.get('pk')
        if pk:
            supply = MemberSupplyRequest.objects.get(pk=pk)
            pvars = MemberSupplyRequestVariation.objects.filter(supply_request=supply)
            initial = [{'breed': x.breed, 'total': x.total} for x in pvars]
            extra = 0 if len(initial) > 0 else 1
        form = MemberSupplyRequestForm(request.POST, request=request, instance=supply)
        variation_formset = formset_factory(MemberSupplyRequestVariationForm, formset=VariationSupplyRequestFormSet, extra=extra)
        variation_form = variation_formset(request.POST, prefix='variation', initial=initial)
        if form.is_valid() and variation_form.is_valid():
            try:
                with transaction.atomic():
                    
                    req = form.save(commit=False)
                    if not pk:
                        req.transaction_reference = generate_alpanumeric(prefix="SR", size=8)
                    req.created_by = request.user
                    req.save()
                    if pk:
                        MemberSupplyRequestVariation.objects.filter(supply_request=req).delete()
                    for c in variation_form:
                        if len(c.cleaned_data) > 0:
                            cf = c.save(commit=False)
                            cf.supply_request = req
                            cf.created_by = request.user
                            cf.save()
                    
                    try:
                        message = message_template().supply_request
                        message = message.replace('<NAME>', req.cooperative_member.surname)
                        message = message.replace('<NUMBER>', '%s' % req.get_sum_total())
                        message = message.replace('<DATE>', '%s' % req.supply_date)
                        message = message.replace('<REFERENCE>', req.transaction_reference)
                        sendMemberSMS(self.request, req.cooperative_member, message)
                    except Exception:
                        log_error()
                    return redirect('coop:request_list')
                    
            except Exception as e:
                form.add_error(None, "Supply Request Error! Contact Admin")
                log_error()
        return render(request, self.template_name, {'form': form, 'variation_form': variation_form, 'active': ['_coop_supply_request', '']})
      
    
class MemberSupplyRequestDetailView(FormMixin, DetailView):
    model = MemberSupplyRequest
    form_class = MemberSupplyRequestConfirmForm
    
    def get_success_url(self):
        return reverse('coop:request_list')
    
    def get_context_data(self, **kwargs):
        context = super(MemberSupplyRequestDetailView, self).get_context_data(**kwargs)
        context['active'] = ['_coop_supply_request', '']
        instance = MemberSupplyRequest.objects.get(pk=self.kwargs.get('pk'))
        context['form'] = MemberSupplyRequestConfirmForm(instance = instance)
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        instance = MemberSupplyRequest.objects.get(pk=self.kwargs.get('pk'))
        form = MemberSupplyRequestConfirmForm(request.POST, instance = instance)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # Here, we would record the user's interest using the message
        # passed in form.cleaned_data['message']
        form.instance.confirmation_logged_by = self.request.user
        form.save()
        
        try:
            message = message_template().supply_confirmation
            if form.instance.status == 'ACCEPTED':
                message = message.replace('<NAME>', form.instance.cooperative_member.surname)
                message = message.replace('<DATE>', '%s' % form.instance.supply_date)
                message = message.replace('<REFERENCE>', form.instance.transaction_reference)
                
            else:
                message = message_template().supply_cancelled
                message = message.replace('<NAME>', form.instance.cooperative_member.surname)
                message = message.replace('<REFERENCE>', form.instance.transaction_reference)
            sendMemberSMS(self.request, form.instance.cooperative_member, message)
        except Exception:
            log_error()
        messages.success(self.request, 'Request %s Confirmed' % form.instance.transaction_reference)
        return super(MemberSupplyRequestDetailView, self).form_valid(form)


class SupplyConfirmationView(UpdateView):
    model = MemberSupplyRequest
    form_class = MemberSupplyRequestConfirmForm
    
    def get_context_data(self, **kwargs):
        context = super(SupplyConfirmationView, self).get_context_data(**kwargs)
        context['active'] = ['_coop_supply_request', '']
        return context


class MembersMapView(TemplateView):
    template_name = "coop/farmer_map.html"


def get_farmer_map(request):
    farmer = CooperativeMember.objects.all()
    data = []
    for f in farmer:
        if f.gps_coodinates:
            data.append({"name": f.get_name(), "gps": f.gps_coodinates})
    print(data)
    return JsonResponse(data, safe=False)


#Phone number Register
class RegisteredSimcardsListView(ListView):
    model = RegisteredSimcards
    template_name = "coop/registersimcards_list.html"
    ordering = ['-create_date']
    extra_context = {'active': ['_savings']}

    def dispatch(self, *args, **kwargs):
        if self.request.GET.get('download'):
            return self.download_file()
        return super(RegisteredSimcardsListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        queryset = super(RegisteredSimcardsListView, self).get_queryset()
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        search = self.request.GET.get('search')

        if search:
            queryset = queryset.filter(Q(name__icontains=search)|Q(phone_number__icontains=search))
        if start_date and end_date:
            queryset = queryset.filter(registration_date__gte = start_date, registration_date__lte = end_date)
        if start_date:
            queryset = queryset.filter(registration_date = start_date)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(RegisteredSimcardsListView, self).get_context_data(**kwargs)
        context['form'] = RegisteredSimcardsFilterForm(self.request.GET)
        return context

    def download_file(self, *args, **kwargs):

        _value = []
        columns = []
        queryset = super(RegisteredSimcardsListView, self).get_queryset()
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        search = self.request.GET.get('search')

        profile_choices = ['user_id', 'name', 'registration_date', 'sex',
                           'phone_number', 'district', 'created_by__username']

        columns += [self.replaceMultiple(c, ['_', '__name'], ' ').title() for c in profile_choices]
        # Gather the Information Found
        # Create the HttpResponse object with Excel header.This tells browsers that
        # the document is a Excel file.
        response = HttpResponse(content_type='application/ms-excel')

        # The response also has additional Content-Disposition header, which contains
        # the name of the Excel file.
        response['Content-Disposition'] = 'attachment; filename=RegisteredNumbers%s.xls' % datetime.now().strftime(
            '%Y%m%d%H%M%S')

        # Create object for the Workbook which is under xlwt library.
        workbook = xlwt.Workbook()

        # By using Workbook object, add the sheet with the name of your choice.
        worksheet = workbook.add_sheet("Members")

        row_num = 0
        style_string = "font: bold on; borders: bottom dashed"
        style = xlwt.easyxf(style_string)

        for col_num in range(len(columns)):
            # For each cell in your Excel Sheet, call write function by passing row number,
            # column number and cell data.
            worksheet.write(row_num, col_num, columns[col_num], style=style)

        queryset = RegisteredSimcards.objects.values(*profile_choices).all()

        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(phone_number__icontains=search))
        if start_date and end_date:
            queryset = queryset.filter(registration_date__gte=start_date, registration_date__lte=end_date)
        if start_date:
            queryset = queryset.filter(registration_date=start_date)

        for m in queryset:

            row_num += 1
            ##print profile_choices
            row = [
                m['%s' % x] if 'registration_date' not in x else m['%s' % x].strftime('%d-%m-%Y') if m.get('%s' % x) else ""
                for x in profile_choices]

            for col_num in range(len(row)):
                worksheet.write(row_num, col_num, row[col_num])
        workbook.save(response)
        return response

    def replaceMultiple(self, mainString, toBeReplaces, newString):
        # Iterate over the strings to be replaced
        for elem in toBeReplaces:
            # Check if string is in the main string
            if elem in mainString:
                # Replace the string
                mainString = mainString.replace(elem, newString)

        return mainString


class RegisteredSimcardsCreateView(CreateView):
    model = RegisteredSimcards
    form_class = RegisteredSimcardsForm
    extra_context = {'active': ['_member'], 'title': "Register Simcards"}
    template_name = "coop/general_form.html"
    success_url = reverse_lazy('coop:phonenumberregister_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # if form.instance.member:
        #     harvested_quantity = form.instance.member.sunflower_acreage if form.instance.member.sunflower_acreage else 0
        #     harvested_quantity_new = harvested_quantity + form.instance.acreage
        #     form.instance.member.sunflower_acreage = harvested_quantity_new
        #     form.instance.member.save()
        return super(RegisteredSimcardsCreateView, self).form_valid(form)


class RegisteredSimcardsUpdateView(UpdateView):
    model = RegisteredSimcards
    form_class = RegisteredSimcardsForm
    template_name = "coop/general_form.html"
    success_url = reverse_lazy('coop:phonenumberregister_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super(RegisteredSimcardsUpdateView, self).form_valid(form)


class RegisteredSimcardsDeleteView(DeleteView):
    model = RegisteredSimcards
    template_name = "confirm_delete.html"
    success_url = reverse_lazy('coop:phonenumberregister_list')

    def get_context_data(self, **kwargs):
        context = super(RegisteredSimcardsDeleteView, self).get_context_data(**kwargs)
        deletable_objects, model_count, protected = get_deleted_objects([self.object])
        context['deletable_objects'] = deletable_objects
        context['model_count'] = dict(model_count).items()
        context['protected'] = protected
        return context


class RegisteredSimcardsUploadView(View):

    template_name = 'coop/phone_reg_upload.html'

    def get(self, request, *args, **kwargs):
        data = {"title": "Registered Simcards"}
        data['form'] = RegisteredSimcardsUploadForm
        return render(request, self.template_name, data)

    def post(self, request, *args, **kwargs):
        data = dict()
        form = RegisteredSimcardsUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['excel_file']
            path = f.temporary_file_path()
            index = int(form.cleaned_data['sheet']) - 1
            startrow = int(form.cleaned_data['row']) - 1

            date_col = int(form.cleaned_data['date_col'])
            farmer_reference_col = int(form.cleaned_data['farmer_reference_col'])
            sex_col = int(form.cleaned_data['sex_col'])
            phone_number_col = int(form.cleaned_data['phone_number_col'])
            district_col = int(form.cleaned_data['district_col'])

            book = xlrd.open_workbook(filename=path, logfile='/tmp/xls.log')
            sheet = book.sheet_by_index(index)
            rownum = 0
            data = dict()
            order_list = []
            member = None

            for i in range(startrow, sheet.nrows):
                try:
                    row = sheet.row(i)
                    rownum = i + 1

                    registration_date = (row[date_col].value)
                    if registration_date:
                        try:
                            date_str = datetime(*xlrd.xldate_as_tuple(registration_date, book.datemode))
                            registration_date = date_str.strftime("%Y-%m-%d")
                        except Exception as e:
                            data['errors'] = '"%s" is not a valid Order Date (row %d): %s' % \
                                             (registration_date, i + 1, e)
                            return render(request, self.template_name,
                                          {'active': 'system', 'form': form, 'error': data})

                    farmer_reference = smart_str(row[farmer_reference_col].value).strip()
                    if not re.search('^[A-Z0-9\s\(\)\-\.\/\']+$', farmer_reference, re.IGNORECASE):
                        if (i + 1) == sheet.nrows: break
                        data['errors'] = '"%s" is not a valid Farmer Name (row %d)' % \
                                         (farmer_reference, i + 1)
                        return render(request, self.template_name,
                                      {'active': 'system', 'form': form, 'error': data})

                    sex = smart_str(row[sex_col].value).strip()
                    if not re.search('^[A-Z]+$', sex, re.IGNORECASE):
                        if (i + 1) == sheet.nrows: break
                        data['errors'] = '"%s" is not a valid Sex(row %d)' % \
                                         (sex, i + 1)
                        return render(request, self.template_name,
                                      {'active': 'system', 'form': form, 'error': data})

                    phone_number = smart_str(row[phone_number_col].value).strip()
                    if not re.search('^[0-9\.]+$', phone_number, re.IGNORECASE):
                        if (i + 1) == sheet.nrows: break
                        data['errors'] = '"%s" is not a valid Phone Number (row %d)' % \
                                         (phone_number, i + 1)
                        return render(request, self.template_name,
                                      {'active': 'system', 'form': form, 'error': data})

                    district = smart_str(row[district_col].value).strip()
                    if not re.search('^[A-Z\.]+$', district, re.IGNORECASE):
                        if (i + 1) == sheet.nrows: break
                        data['errors'] = '"%s" is not a valid District (row %d)' % \
                                         (district, i + 1)
                        return render(request, self.template_name,
                                      {'active': 'system', 'form': form, 'error': data})

                    order_list.append({"registration_date": registration_date,
                                       "farmer": farmer_reference,
                                       "sex": sex,
                                       "phone_number": phone_number,
                                       "district": district
                                       })

                except Exception as err:
                    log_error()
                    return render(request, self.template_name, {'active': 'setting', 'form': form, 'error': err})

            print(order_list)
            if order_list:
                try:
                    with transaction.atomic():
                        for order_i in order_list:
                            registration_date = order_i.get("registration_date")
                            farmer_reference = order_i.get("farmer")
                            sex = order_i.get("sex")
                            phone_number = order_i.get("phone_number")
                            district = order_i.get("district")

                            RegisteredSimcards.objects.create(
                                registration_date=registration_date,
                                name=farmer_reference,
                                sex=sex,
                                phone_number=phone_number,
                                district=district,
                                created_by=request.user
                            )

                        return redirect('coop:phonenumberregister_list')
                except Exception as e:
                    log_error()
                    return render(request, self.template_name, {'active': 'setting', 'form': form, 'error': e})
            return render(request, self.template_name, {'active': 'setting', 'form': form, 'data': data})
