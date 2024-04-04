from __future__ import unicode_literals
import re
import json
import xlrd
import xlwt
import datetime

from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.encoding import smart_str
from django.forms.formsets import formset_factory, BaseFormSet
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from userprofile.models import Profile, AccessLevel
from credit.utils import create_loan_transaction
from credit.models import CreditManager, LoanRequest, CreditManagerAdmin, LoanTransaction
from credit.forms import CreditManagerForm, CreditManagerUserForm, LoanUploadForm

from coop.utils import credit_member_account, debit_member_account
from coop.models import MemberOrder, CooperativeMember, OrderItem
from conf.utils import generate_alpanumeric, genetate_uuid4, log_error, log_debug, generate_numeric, float_to_intstring, \
    get_deleted_objects, \
    get_message_template as message_template

from credit.RawFinancialAPI import RawFinancial


class ExtraContext(object):
    extra_context = {}

    def get_context_data(self, **kwargs):
        context = super(ExtraContext, self).get_context_data(**kwargs)

        context.update(self.extra_context)
        return context


class CreditManagerListView(ExtraContext, ListView):
    model=CreditManager
    extra_context = {'active': ['_credit', '__cm']}


class CreditManagerCreateView(ExtraContext, CreateView):
    model = CreditManager
    form_class = CreditManagerForm
    success_url = reverse_lazy('credit:cm_list')
    extra_context = {'active': ['_credit', '__cm']}

    def get_initial(self):
        initial = super(CreditManagerCreateView, self).get_initial()
        initial['instance'] = None
        return initial


class CreditManagerUpdateView(CreditManagerCreateView, UpdateView):
    pass


class CreditManagerAdminCreateView(CreateView):
    model = CreditManager
    form_class = CreditManagerUserForm
    template_name = "credit/cm_user_form.html"
    extra_context = {'active': ['__cm']}
    success_url = reverse_lazy('credit:cm_list')

    def form_valid(self, form):
        # f = super(SupplierUserCreateView, self).form_valid(form)
        instance = None
        try:
            while transaction.atomic():
                self.object = form.save()
                if not instance:
                    self.object.set_password(form.cleaned_data.get('password'))
                self.object.save()
                pk = self.kwargs.get('cm')
                cm = get_object_or_404(CreditManager, pk=pk)
                profile = get_object_or_404(Profile, pk= self.object.id)

                profile.msisdn=form.cleaned_data.get('msisdn')
                profile.access_level=get_object_or_404(AccessLevel, name='CREDIT_MANAGER')
                profile.save()

                CreditManagerAdmin.objects.create(
                    user=self.object,
                    credit_manager = cm,
                    created_by =self.request.user
                )
        except Exception as e:
            print(e)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(CreditManagerAdminCreateView, self).get_context_data(**kwargs)
        pk = self.kwargs.get('cm')
        context['cm'] = get_object_or_404(CreditManager, pk=pk)
        return context

    def get_initial(self):
        initial = super(CreditManagerAdminCreateView, self).get_initial()
        initial['instance'] = None
        return initial

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(CreditManagerAdminCreateView, self).get_form_kwargs(*args, **kwargs)
        kwargs['instance'] = None
        return kwargs


class CreditManagerAdminListView(ExtraContext, ListView):
    model = CreditManagerAdmin
    extra_context = {'active': ['__cm']}

    def get_context_data(self, **kwargs):
        context = super(CreditManagerAdminListView, self).get_context_data(**kwargs)
        context['cm'] = self.kwargs.get('cm')
        return context


class LoanRequestListView(ExtraContext, ListView):
    model=LoanRequest
    extra_context = {'active': ['_credit', '__loan']}
    ordering = ('-id')


class LoanRequestDetailView(ExtraContext, DetailView):
    model = LoanRequest
    extra_context = {'active': ['_credit', '__loan']}
    ordering = ('-id',)


class ApproveLoan(View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        status = self.kwargs.get('status')
        today = datetime.datetime.today()
        try:
            lq = LoanRequest.objects.get(pk=pk)
            if status == 'APPROVED':
                lq.confirm_date = today
                OrderItem.objects.filter(pk=lq.order_item.id).update(status="APPROVED")
                params = {
                    "loan": lq,
                    "member": lq.member,
                    "credit_manager": lq.credit_manager,
                    "amount": lq.requested_amount,
                    "transaction_type": 'DEBIT',
                    "created_by": request.user,
                }
                amt = create_loan_transaction(params)
                pl = {
                    "member": lq.member,
                    "amount": amt,
                    "entry_type": "CREDIT",
                    "transaction_category": "LOAN",
                    "description": "Loan request approved",
                    "created_by": request.user,
                }
                credit_member_account(pl)

                pld = {
                    "member": lq.member,
                    "amount": amt,
                    "entry_type": "DEBIT",
                    "transaction_category": "ORDER",
                    "description": "Order for item %s" % (lq.order_item.item.name),
                    "created_by": request.user,
                }
                debit_member_account(pld)

            if status == 'REJECTED':
                lq.confirm_date = today
            if status == "STATUS":
                status = lq.status
                rf = RawFinancial()
                st = rf.loan_status(lq.loan_request_id)
                if "loan_status" in st:
                    lq.response = "{} <br>======<br> {}".format(lq.response, st)
                    if st['loan_status'] == "rejected":
                        status = "REJECTED"
                    if st['loan_status'] == "approved":
                        status = "APPROVED"
                        lq.confirm_date = today
                        OrderItem.objects.filter(pk=lq.order_item.id).update(status="APPROVED")
                        params = {
                            "loan": lq,
                            "member": lq.member,
                            "credit_manager": lq.credit_manager,
                            "amount": lq.requested_amount,
                            "transaction_type": 'DEBIT',
                            "created_by": request.user,
                        }
                        amt = create_loan_transaction(params)
                        pl = {
                            "member": lq.member,
                            "amount": amt,
                            "entry_type": "CREDIT",
                            "transaction_category": "LOAN",
                            "description": "Loan request approved",
                            "created_by": request.user,
                        }
                        credit_member_account(pl)

                        pld = {
                            "member": lq.member,
                            "amount": amt,
                            "entry_type": "DEBIT",
                            "transaction_category": "ORDER",
                            "description": "Order for item %s" % (lq.order_item.item.name),
                            "created_by": request.user,
                        }
                        debit_member_account(pld)
            lq.status = status
            lq.save()
        except Exception as e:
            log_error()

        return redirect('credit:loan_detail', pk)


class LoanTransactionListView(ExtraContext, ListView):
    model=LoanTransaction
    extra_context = {'active': ['_credit', '__loan_transaction']}
    ordering = ('-id')


class LoanRequestUploadView(ExtraContext, View):
    template_name = "credit/loan_upload_view.html"

    def get(self, request, **kwargs):
        context = dict()
        form = LoanUploadForm
        context['form'] = form
        return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        context = dict()
        form = LoanUploadForm(request.POST, request.FILES)

        if form.is_valid():
            f = request.FILES['excel_file']

            path = f.temporary_file_path()
            index = int(form.cleaned_data['sheet']) - 1
            startrow = int(form.cleaned_data['row']) - 1

            last_name_col = int(form.cleaned_data['last_name_col'])
            first_name_col = int(form.cleaned_data['first_name_col'])
            phone_number_col = int(form.cleaned_data['phone_number_col'])
            village_col = int(form.cleaned_data['village_col'])
            district_col = int(form.cleaned_data['district_col'])
            loan_amount_col = int(form.cleaned_data['loan_amount_col'])

            book = xlrd.open_workbook(filename=path, logfile='/tmp/xls.log')
            sheet = book.sheet_by_index(index)
            rownum = 0
            data = dict()
            payment_list = []
            member = None

            for i in range(startrow, sheet.nrows):
                try:
                    row = sheet.row(i)
                    rownum = i + 1

                    last_name = smart_str(row[last_name_col].value).strip()
                    first_name = smart_str(row[first_name_col].value).strip()
                    phone_number = smart_str(row[phone_number_col].value).strip()
                    village = smart_str(row[village_col].value).strip()
                    district = smart_str(row[district_col].value).strip()
                    loan_amount = smart_str(row[loan_amount_col].value).strip()

                    if not re.search('^[0-9\.]+$', loan_amount, re.IGNORECASE):
                        data['errors'] = '"%s" is not a valid Amount Figure (row %d)' % (loan_amount, i + 1)
                        print(data)
                        return render(request, self.template_name, {'active': 'system', 'form': form, 'error': data})

                    member = CooperativeMember.objects.filter(
                        surname=last_name,
                        first_name=first_name,
                        district__name=district
                    )
                    print(last_name)

                    q = {'member': member,
                         'loan_amount': loan_amount,
                         'phone_number': phone_number,
                         }
                    payment_list.append(q)


                except Exception as err:
                    log_error()
                    print(err)
                    return render(request, self.template_name, {'active': 'setting', 'form':form, 'error': err})

            print(payment_list)
            if payment_list:
                with transaction.atomic():
                    try:
                        do = None

                        for c in payment_list:
                            member = nc.get('member')
                            requested_amount = nc.get('loan_amount')
                            request_date = nc.get('request_date') if c.get('date_of_birth') != '' else None
                            phone_number = nc.get('phone_number')


                            LoanRequest.objects.create(
                                reference=generate_alpanumeric(AMT,9),
                                member=member,
                                requested_amount=requested_amount,
                                request_date=request_date
                            )
                        return redirect('credit:loan_list')
                    except Exception as err:
                        log_error()
                        data['error'] = err
        return render(request, self.template_name, context)
