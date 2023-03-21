# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import xlrd
import datetime
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.encoding import smart_str
from django.db import transaction
from django.db.models import Count, Q
from django.views.generic import View, ListView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from conf.utils import log_debug, log_error, get_deleted_objects, get_consontant_upper
from conf.models import District, County, SubCounty
from coop.models import *
from coop.forms import *
from userprofile.models import Profile, AccessLevel


class ExtraContext(object):
    extra_context = {}

    def get_context_data(self, **kwargs):
        context = super(ExtraContext, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context


class AgentListView(ExtraContext, ListView):
    template_name = 'coop/agents_list.html'

    def get(self, request, **kwargs):

        name = self.request.GET.get('name')
        phone_number = self.request.GET.get('phone_number')
        cooperative = self.request.GET.get('cooperative')
        end_date = self.request.GET.get('end_date')
        start_date = self.request.GET.get('start_date')

        agents = Agent.objects.all()
        if phone_number:
            agents = agents.filter(phone_number=phone_number)

        if name:
            agents = agents.filter(Q(user__first_name__icontains=name) | Q(user__last_name__icontains=name))

        if self.request.user.profile.district.all().count() > 0:
            agents = agents.filter(district__id__in=self.request.user.profile.district.all())

        agent_summary = []
        for a in agents:
            queryset = CooperativeMember.objects.filter(create_by=a.user)

            if start_date:
                queryset = queryset.filter(create_date__gte=start_date)

            if end_date:
                queryset = queryset.filter(create_date__lte=end_date)

            if cooperative:
                queryset = queryset.filter(cooperative_id=cooperative)
            agent_summary.append({'agent': a, 'members': queryset.count()})


        data = {
            'agent_summary': agent_summary,
            'form': AgentSearchForm(request.GET),
            'active': ['_agent']
        }
        return render(request, self.template_name, data)


class AgentCreateFormView(ExtraContext, FormView):
    template_name = "coop/agent_form.html"
    form_class = AgentForm
    extra_context = {'active': ['_agent']}
    success_url = reverse_lazy('coop:agent_list')

    def form_valid(self, form):

        # f = super(SupplierUserCreateView, self).form_valid(form)
        instance = None
        try:
            while transaction.atomic():
                self.object = form.save()
                if not instance:
                    self.object.set_password(form.cleaned_data.get('password'))
                self.object.save()

                profile = self.object.profile

                profile.msisdn=form.cleaned_data.get('msisdn')
              
                profile.access_level=get_object_or_404(AccessLevel, name="AGENT")
                profile.save()
                
                fgs = form.cleaned_data.get('farmer_group')
                districts = form.cleaned_data.get('district')
                for district in districts:
                    profile.district.add(district)

                for fg in fgs:
                    FarmerGroupAdmin.objects.create(
                        user=self.object,
                        farmer_group = get_object_or_404(FarmerGroup, pk=fg),
                        created_by =self.request.user
                    )
                return super(AgentCreateFormView, self).form_valid(form)
        except Exception as e:
            form.add_error(None, 'Error: %s.' % e)
            log_error()
            return super(AgentCreateFormView, self).form_invalid(form)


class AgentUpdateFormView(ExtraContext, UpdateView):
    model = User
    template_name = "coop/agent_form.html"
    form_class = AgentUpdateForm
    extra_context = {'active': ['_agent']}
    success_url = reverse_lazy('coop:agent_list')

    # def get_form(self, form_class):
    #     form = super(AgentUpdateFormView, self).get_form(form_class)
    #
    def form_invalid(self, form):
        print('Error')
        return super(AgentUpdateFormView, self).form_invalid(form)

    def form_valid(self, form):
        # f = super(SupplierUserCreateView, self).form_valid(form)
        print('FF')
        instance = None
        try:
            while transaction.atomic():
                super(AgentUpdateFormView, self).form_valid(form)
                # self.object = form.save()
                if not instance:
                    self.object.set_password(form.cleaned_data.get('password'))
                    self.object.save()

                profile = self.object.profile

                profile.msisdn=form.cleaned_data.get('msisdn')

                profile.access_level=get_object_or_404(AccessLevel, name="AGENT")
                profile.save()

                fgs = form.cleaned_data.get('farmer_group')

                districts = form.cleaned_data.get('district')
                if districts:
                    profile.district.clear()
                    for district in districts:
                        print(district)
                        profile.district.add(district)
                        profile.save()

                FarmerGroupAdmin.objects.filter(user=self.object).delete()
                for fg in fgs:
                    FarmerGroupAdmin.objects.create(
                        user=self.object,
                        farmer_group = get_object_or_404(FarmerGroup, pk=fg),
                        created_by =self.request.user
                    )
                return redirect('coop:agent_list')
        except Exception as e:
            log_error()
            form.add_error(None, 'Error: %s.' % e)
            return super(AgentUpdateFormView, self).form_invalid(form)

    def get_initial(self):
        initial = super(AgentUpdateFormView, self).get_initial()
        user = User.objects.get(pk=self.kwargs.get('pk'))
        fgs=FarmerGroupAdmin.objects.filter(user=user)
        initial['msisdn'] = user.profile.msisdn
        initial['farmer_group'] = [i.farmer_group.id for i in fgs]
        initial['district'] = [d.id for d in user.profile.district.all()]

        return initial
    #
    # def get_form_kwargs(self):
    #     kwargs = super(AgentUpdateFormView, self).get_form_kwargs()
    #     kwargs['instance'] = User.objects.get(pk=self.kwargs.get('pk'))
    #     return kwargs


class AgentUploadView(View):
    template_name = 'coop/upload_agents.html'

    def get(self, request, *arg, **kwargs):
        data = dict()
        data['form'] = AgentUploadForm()
        data['active'] = ['_agent']
        return render(request, self.template_name, data)

    def post(self, request, *args, **kwargs):
        data = dict()
        form = AgentUploadForm(request.POST, request.FILES)
        if form.is_valid():

            f = request.FILES['excel_file']

            path = f.temporary_file_path()
            index = int(form.cleaned_data['sheet']) - 1
            startrow = int(form.cleaned_data['row']) - 1
            name_col = int(form.cleaned_data['name_col'])
            email_column = int(form.cleaned_data['email_column'])
            phone_number_col = int(form.cleaned_data['phone_number_col'])
            district_col = int(form.cleaned_data['district_col'])
            username_col = int(form.cleaned_data['username_col'])
            password_col = int(form.cleaned_data['password_col'])

            book = xlrd.open_workbook(filename=path, logfile='/tmp/xls.log')
            sheet = book.sheet_by_index(index)
            rownum = 0
            data = dict()
            agent_list = []
            for i in range(startrow, sheet.nrows):
                try:
                    row = sheet.row(i)
                    rownum = i + 1
                    name = smart_str(row[name_col].value).strip()

                    if not re.search('^[0-9A-Z\s\(\)\-\.]+$', name, re.IGNORECASE):
                        data['errors'] = '"%s" is not a valid Name (row %d)' % \
                                         (name, i + 1)
                        return render(request, self.template_name, {'active': 'system', 'form': form, 'error': data})

                    email = smart_str(row[email_column].value).strip()

                    if email:
                        if not re.search('^[A-Z\s\(\)\-\.]+$', email, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid Email (row %d)' % \
                                             (email, i + 1)
                            return render(request, self.template_name,
                                          {'active': 'system', 'form': form, 'error': data})


                    phone_number = smart_str(row[phone_number_col].value).strip()

                    if phone_number:
                        try:
                            phone_number = int(row[phone_number_col].value)
                        except Exception:
                            data['errors'] = '"%s" is not a valid Phone number (row %d)' % \
                                             (phone_number, i + 1)
                            return render(request, self.template_name,
                                          {'active': 'system', 'form': form, 'error': data})

                    district = smart_str(row[district_col].value).strip()

                    if district:
                        if not re.search('^[A-Z\s\(\)\-\.]+$', district, re.IGNORECASE):
                            data['errors'] = '"%s" is not a valid District (row %d)' % \
                                             (district, i + 1)
                            return render(request, self.template_name,
                                          {'active': 'system', 'form': form, 'error': data})

                    username = smart_str(row[username_col].value).strip()

                    if not username:
                        data['errors'] = 'Username is missing at (row %d)' % \
                                         (i + 1)
                        return render(request, self.template_name,
                                      {'active': 'system', 'form': form, 'error': data})

                    password = smart_str(row[password_col].value).strip()

                    if not password:
                        data['errors'] = 'Password is missing at (row %d)' % \
                                         (i + 1)
                        return render(request, self.template_name,
                                      {'active': 'system', 'form': form, 'error': data})

                    q = {'name': name, 'email': email, 'username': username, 'password': password, 'phone_number': phone_number, 'district': district,}
                    agent_list.append(q)

                except Exception as err:
                    log_error()
                    return render(request, self.template_name, {'active': 'setting', 'form': form, 'error': '%s on (row %d)' % (err, i + 1)})
            if agent_list:
                with transaction.atomic():
                    try:
                        for c in agent_list:

                            do = None

                            name = c.get('name').split(' ')
                            surname = name[0]
                            first_name = name[1] if len(name) > 1 else None
                            other_name = name[2] if len(name) > 2 else None
                            email = c.get('email')
                            username = c.get('username')
                            password = c.get('password')
                            phone_number = c.get('phone_number')

                            if district:
                                dl = [dist for dist in District.objects.filter(name__iexact=district)]
                                do = dl[0] if len(dl) > 0 else None

                            if not User.objects.filter(username=username).exists():
                                user = User.objects.create(
                                    first_name=first_name,
                                    last_name=surname,
                                    email=email,
                                    username=username,
                                    is_active=True,
                                )

                                user.set_password(password)
                                user.save()

                                profile = user.profile
                                profile.msisdn = phone_number
                                profile.district.add(do)
                                profile.access_level = get_object_or_404(AccessLevel, name="AGENT")
                                profile.save()

                        return redirect('coop:agent_list')
                    except Exception as err:
                        log_error()
                        data['error'] = err

        data['form'] = form
        data['active'] = ['_agent']
        return render(request, self.template_name, data)