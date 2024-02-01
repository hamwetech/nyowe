import re
import xlrd
import json
from datetime import datetime
from django.utils.encoding import smart_str
from django.shortcuts import render
from django.views.generic import View, ListView
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse

from conf.utils import internationalize_number, log_debug, log_error
from messaging.utils import sendSMS
from messaging.models import OutgoingMessages
from messaging.forms import SendMessageForm, MessageLogUploadForm, MessageSearchForm


class OutGoingMessageListView(ListView):
    model = OutgoingMessages
    ordering = ['-sent_date']
    
    def get_context_data(self, **kwargs):
        context = super(OutGoingMessageListView, self).get_context_data(**kwargs)
        context['form'] = MessageSearchForm(self.request.GET)
        context['active'] = ['_messaging', '__sent']
        return context

    def get_queryset(self):
        queryset = super(OutGoingMessageListView, self).get_queryset()
        search = self.request.GET.get('search')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if search:
            queryset = queryset.filter(msisdn__icontains=search)
        if start_date:
            queryset = queryset.filter(sent_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(sent_date__lte="%s %s" % (end_date, "23:59:59"))
        return queryset

    
    
class SendMessageView(View):

    def dispatch(self, *args, **kwargs):
        return super(SendMessageView, self).dispatch(*args, **kwargs)

    template_name = 'messaging/send_message.html'

    def get(self, request, *args, **kwargs):
        form = SendMessageForm()
        data = {
            'form': form,
            'active': ['_messaging', '__send']
        }
        return render(request, self.template_name, data)

    def post(self, request, *args, **kwargs):
        form = SendMessageForm(request.POST, request.FILES)
        errors = dict()
        count = 0
        
        if form.is_valid():
            if form.cleaned_data['msisdn_file']:
                
                f = request.FILES['msisdn_file']
                path = f.temporary_file_path()
                message = form.cleaned_data['message']
                sender_id = form.cleaned_data['sender_id']
                index = int(form.cleaned_data['sheetno']) - 1
                startrow = int(form.cleaned_data['startrow']) - 1
                msisdn_col = int(form.cleaned_data['msisdn_col'])
                name_col = int(form.cleaned_data['name_col'])
                field3_col = int(form.cleaned_data['field3_col'])
                field4_col = int(form.cleaned_data['field4_col'])

                try:
                    book = xlrd.open_workbook(filename=path, logfile='/tmp/xls.log')
                    sheet = book.sheet_by_index(index)
                    numbers = []

                    for i in range(startrow, sheet.nrows):
                        message = form.cleaned_data['message']
                        network = None
                        row = sheet.row(i)
                        msisdn = None
                        msisdn_detail = None

                        try:
                            msisdn = int(row[msisdn_col].value)
                            msisdn = internationalize_number(msisdn)
                        except Exception as err:
                            errors['error'] = "Invalid Number '%s' at ROW: %d. Please make sure the numbers are in the right column" % (
                            row[msisdn_col].value, i + 1)

                        try:
                            field1 = smart_str(row[name_col].value).strip()
                        except:
                            field1 = None
                        
                        try:
                            field3 = smart_str(row[field3_col].value).strip()
                        except:
                            field3 = None
                        try:
                            field4 = smart_str(row[field4_col].value).strip()
                        except:
                            field4 = None
                        try:
                            
                            if field1: message = message.replace("<NAME>", field1)
                            if field3: message = message.replace("<FIELD3>", str(field3))
                            if field4: message = message.replace("<FIELD4>", str(field4))
                        except UnicodeDecodeError as err:
                            errors['error'] = "Encode Error: %s " % err

                        numbers.append({'msisdn': msisdn, 'message': message})
                except Exception as err:
                    errors['error'] = "Error: %s " % err

            else:
                
                msisdn = form.cleaned_data['msisdn']
                message = form.cleaned_data['message']
                sender_id = form.cleaned_data['sender_id']
                
                v = 0
                numbers = []
                
                try:
                    for m in re.split("\r\n|,| ", msisdn):
                        if m:
                            try:
                                #m = unicodedata.normalize('NFKD', m).encode('ascii', 'ignore')
                                m = internationalize_number(m)
                            except ValueError as err:
                                errors['error'] = "Invalid Phone Number %s" % m
    
                            numbers.append({'msisdn': m, 'message': message})
                except Exception as err:
                    errors['error'] = "Error Occured: %s" % err

            if 'error' in errors:
                data = {
                    'form': form,
                    'errors': errors,
                    'active': 'send_sms'
                }
                return render(request, self.template_name, data)
            count_t = len(numbers)
            
            for d in numbers:
                phone_number = d['msisdn']
                msg = d['message']
                
                sendSMS(request, phone_number, message)
                # res = json.loads(send)
            return redirect('messaging:message_list')
        
        data = {
            'form': form,
            'active': ['_messaging', '__send']
        }
        return render(request, self.template_name, data)


class MessageLogUploadView(View):

    template_name = 'messaging/upload_logs.html'

    def get(self, reqeust, *args, **kwargs):
        data = {}
        data['form'] = MessageLogUploadForm
        return render(reqeust, self.template_name, data)

    def post(self, request, *args, **kwargs):
        data = dict()
        form = MessageLogUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['msisdn_file']

            path = f.temporary_file_path()
            index = int(form.cleaned_data['sheetno']) - 1
            startrow = int(form.cleaned_data['startrow']) - 1

            contact_col = int(form.cleaned_data['contact_col'])
            message_col = int(form.cleaned_data['message_col'])
            status_col = int(form.cleaned_data['status_col'])
            date_col = int(form.cleaned_data['date_col'])

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

                    contact = smart_str(row[contact_col].value).strip()
                    contact = contact.replace("+", "")
                    message = smart_str(row[message_col].value).strip()
                    status = smart_str(row[status_col].value).strip()
                    date = (smart_str(row[date_col].value).strip())

                    date_str = datetime(*xlrd.xldate_as_tuple(float(date), book.datemode))
                    sent_date = date_str.strftime("%Y-%m-%d %H:%M:%S")

                    OutgoingMessages.objects.create(
                        msisdn=contact,
                        message=message,
                        sent_date=sent_date,
                        status=status
                    )
                except Exception as err:
                    log_error()
                    return render(request, self.template_name, {'active': 'setting', 'form':form, 'error': err})
        return redirect('messaging:message_list')