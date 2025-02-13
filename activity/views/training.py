# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import xlrd
import xlwt
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.encoding import smart_str
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from activity.models import *
from activity.forms import *

from conf.utils import generate_alpanumeric, log_debug, log_error

class ExtraContext(object):
    extra_context = {}

    def get_context_data(self, **kwargs):
        context = super(ExtraContext, self).get_context_data(**kwargs)
        context['active'] = ['_training']
        context['title'] = 'Training'
        context.update(self.extra_context)
        return context

class ThematicAreaCreateView(ExtraContext, CreateView):
    model = ThematicArea
    form_class = ThematicAreaForm
    extra_context = {'active': ['_training', '__thematic']}
    success_url = reverse_lazy('activity:thematic_list')
    
    
class ThematicAreaUpdateView(ExtraContext, UpdateView):
    model = ThematicArea
    form_class = ThematicAreaForm
    extra_context = {'active': ['_training', '__thematic']}
    success_url = reverse_lazy('activity:thematic_list')
    
    
class ThematicAreaListView(ExtraContext, ListView):
    model = ThematicArea
    extra_context = {'active': ['_training', '__thematic']}
    

class TrainingSessionListView(ExtraContext, ListView):
    model = TrainingSession
    extra_context = {'active': ['_training', '__training']}
    ordering = ['-training_start']
    
    def get_queryset(self):
        queryset = super(TrainingSessionListView, self).get_queryset()
        if not self.request.user.profile.is_union():
            cooperative = self.request.user.cooperative_admin.cooperative 
            queryset = queryset.filter(trainer__cooperative_admin__cooperative=cooperative)
        return queryset
    
class TrainingSessionDetailView(ExtraContext, DetailView):
    model = TrainingSession
    extra_context = {'active': ['_training', '__training']}
    

class TrainingCreateView(ExtraContext, CreateView):
    model = TrainingSession
    form_class = TrainingForm
    extra_context = {'active': ['_training', '__training']}
    success_url = reverse_lazy('activity:training_list')
    
    def form_valid(self, form):
        form.instance.training_reference = generate_alpanumeric(prefix="TR", size=8)
        form.instance.created_by = self.request.user
        training = super(TrainingCreateView, self).form_valid(form)
        return training
    
    
class ExternalTrainerCreateView(CreateView):
    model = ExternalTrainer
    form_class = ExternaTrainerForm
    extra_context = {'active': ['_training', '__training']}
    success_url = reverse_lazy('activity:training_create')


class UploadTrainingSessionView(FormView):
    form_class = TrainingUploadForm
    template_name = "activity/training_upload.html"
    success_url = reverse_lazy('activity:training_list')

    def form_valid(self, form):
        f = self.request.FILES['trainees_file']
        reference = generate_alpanumeric(prefix="TR", size=8)
        form.instance.training_reference = reference
        form.instance.created_by = self.request.user

        attendance_list = self.request.FILES['attendance_list']
        training_proof = self.request.FILES['training_proof']

        TrainingPhotos.objects.create(
            title="attendance_list",
            training_reference=reference,
            photo=attendance_list
        )

        TrainingPhotos.objects.create(
            title="training_photo",
            training_reference=reference,
            photo=training_proof
        )

        path = f.temporary_file_path()
        index = int(1) - 1
        startrow = int(2) - 1

        id_col = int(0)
        name_id_col = int(1)
        phonenumber_col = int(2)

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
                name = smart_str(row[name_id_col].value).strip()
                phonenumber = smart_str(row[phonenumber_col].value).strip()

                print(sys_id)
                print(name)

                Trainee.objects.create(
                    name = name,
                    phone_number = phonenumber,
                    user_id = sys_id,
                    training_reference = reference
                )

            except Exception as e:
                log_error()
        return super(UploadTrainingSessionView, self).form_valid(form)

    
