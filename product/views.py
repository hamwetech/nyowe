# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import xlwt
import datetime
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.forms.formsets import formset_factory, BaseFormSet
from django.shortcuts import render, redirect
from django.views.generic import View, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db import transaction

from conf.utils import log_debug, log_error
from product.models import *
from product.forms import *

class ExtraContext(object):
    extra_context = {}

    def get_context_data(self, **kwargs):
        context = super(ExtraContext, self).get_context_data(**kwargs)
        context['active'] = ['_union_prod']
        context['title'] = 'Country'
        context.update(self.extra_context)
        return context
    

class ProductUnitListView(ExtraContext, ListView):
    model = ProductUnit
    
    def get_context_data(self, **kwargs):
        context = super(ProductUnitListView, self).get_context_data(**kwargs)
        context['active'].append('__unit')
        return context
    
    

class ProductUnitCreateView(ExtraContext, CreateView):
    model = ProductUnit
    form_class = ProductUnitForm
    template_name = "product/productunit_form.html"
    success_url = reverse_lazy('product:unit_list')
    # 
    # def form_valid(self, form):
    #     form.instance.created_by = self.request.user
    #     return super(ProductCreateView, self).form_valid(form)
    def get_context_data(self, **kwargs):
        context = super(ProductUnitCreateView, self).get_context_data(**kwargs)
        context['active'].append('__unit')
        return context
    

class ProductUnitUpdateView(ExtraContext, UpdateView):
    model = ProductUnit
    form_class = ProductUnitForm
    template_name = "product/productunit_form.html"
    success_url = reverse_lazy('product:unit_list')
    # 
    # def form_valid(self, form):
    #     form.instance.created_by = self.request.user
    #     return super(ProductUpdateView, self).form_valid(form)
    def get_context_data(self, **kwargs):
        context = super(ProductUnitUpdateView, self).get_context_data(**kwargs)
        context['active'].append('__unit')
        return context
    
    
class ProductVariationListView(ExtraContext, ListView):
    model = Product
    template_name = "product/productvariation_list.html"
    
    def get_context_data(self, **kwargs):
        context = super(ProductVariationListView, self).get_context_data(**kwargs)
        context['active'].append('__product')
        return context
    
    
class ProductVariationView(View):
    template_name = "product/product_variation_form.html"
    
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        prod = None
        var = None
        initial = None
        extra=1
        try:
            if pk:
                extra = 0
                prod = Product.objects.get(pk=pk)
                pvars = ProductVariation.objects.filter(product=prod)
                initial = [{'name': x.name, 'unit': x.unit} for x in pvars]
        except Exception as e:
            log_error()
            return redirect('product:variation_list')
        product_form = ProductForm(instance=prod)
        variation_form = formset_factory(ProductVariationForm, formset=BaseFormSet, extra=extra)
        variation_formset = variation_form(prefix='variation', initial=initial)
        data = {'form': product_form,
                'variation_formset': variation_formset,
                'active': ['_union_prod', '__product']}
        return render(request, self.template_name, data)
    
    def post(self, request, *args, **kwargs ):
        pk = self.kwargs.get('pk')
        prod = None
        var = None
        initial = None
        extra=1
        try:
            if pk:
                extra=1
                prod = Product.objects.get(pk=pk)
                pvars = ProductVariation.objects.filter(product=prod)
                initial = [{'name': x.name, 'unit': x.unit} for x in pvars]
        except Exception as e:
            log_error()
            return redirect('product:variation_list')
        product_form = ProductForm(request.POST, instance=prod)
        variation_form = formset_factory(ProductVariationForm, formset=BaseFormSet, extra=extra)
        variation_formset = variation_form(request.POST, prefix='variation')
        if product_form.is_valid() and variation_formset.is_valid():
            try:
                with transaction.atomic():
                    p = product_form.save(commit=False)
                    p.created_by = request.user
                    p.save()
                    if pk:
                        ProductVariation.objects.filter(product=p).delete()
                    for variation_form in variation_formset:
                        v = variation_form.save(commit=False)
                        v.product = p
                        v.created_by = request.user
                        v.save()
                return redirect('product:variation_list')
            except Exception as e:
                log_error()
        data = {'form': product_form,
                'variation_formset': variation_formset,
                'active': ['_union_prod', '__product']}
        return render(request, self.template_name, data)

# Variation Price
class ProductVariationPriceCreateView(ExtraContext, CreateView):
    model = ProductVariationPrice
    form_class = ProductVariationPriceForm
    template_name = "product/productvariationprice_form.html"
    success_url = reverse_lazy('product:price_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super(ProductVariationPriceCreateView, self).form_valid(form)
    
    
    def get_context_data(self, **kwargs):
        context = super(ProductVariationPriceCreateView, self).get_context_data(**kwargs)
        context['active'].append('__price')
        return context
    

class ProductVariationPriceUpdateView(ExtraContext, UpdateView):
    model = ProductVariationPrice
    form_class = ProductVariationPriceForm
    template_name = "product/productvariationprice_form.html"
    success_url = reverse_lazy('product:price_list')
    # 
    # def form_valid(self, form):
    #     form.instance.created_by = self.request.user
    #     return super(ProductUpdateView, self).form_valid(form)
    def get_context_data(self, **kwargs):
        context = super(ProductVariationPriceUpdateView, self).get_context_data(**kwargs)
        context['active'].append('__price')
        return context
    
    
class ProductVariationPriceListView(ExtraContext, ListView):
    model = ProductVariationPrice
    template_name = "product/productvariationprice_list.html"
    
    def get_context_data(self, **kwargs):
        context = super(ProductVariationPriceListView, self).get_context_data(**kwargs)
        context['active'].append('__price')
        return context
    

class ProductVariationPriceLogListView(ExtraContext, ListView):
    model =  ProductVariationPriceLog
    ordering = '-create_date'
    template_name = "product/productvariationpricelog_list.html"
    
    def get_queryset(self):
        qs = super(ProductVariationPriceLogListView, self).get_queryset()
        if self.kwargs.get('pk'):
            qs = qs.filter(product__pk=self.kwargs.get('pk'))
        return qs
    
    def get_context_data(self, **kwargs):
        context = super(ProductVariationPriceLogListView, self).get_context_data(**kwargs)
        context['active'].append('__price')
        return context
    
def get_product_price(request, pk):
    try:
        pp = ProductVariationPrice.objects.get(product=pk)
        return JsonResponse({"price": pp.price})
    except Exception:
        return JsonResponse({"price": "error"})
   
    
class SupplierCreateView(ExtraContext, CreateView):
    model = Supplier
    form_class = SupplierForm
    extra_context = {'active': ['_union_prod','__supplier']}
    success_url = reverse_lazy('product:supplier_list')
    
    
class SupplierUpdateView(ExtraContext, UpdateView):
    model = Supplier
    form_class = SupplierForm
    extra_context = {'active': ['_union_prod','__supplier']}
    success_url = reverse_lazy('product:supplier_list')
    
    
class SupplierListView(ExtraContext, ListView):
    model = Supplier
    extra_context = {'active': ['_union_prod','__supplier']}
    

class ItemCreateView(ExtraContext, CreateView):
    model = Item
    form_class = ItemForm
    extra_context = {'active': ['_union_prod','__Item']}
    success_url = reverse_lazy('product:item_list')
    
    
class ItemUpdateView(ExtraContext, UpdateView):
    model = Item
    form_class = ItemForm
    extra_context = {'active': ['_union_prod','__Item']}
    success_url = reverse_lazy('product:item_list')
    
    
class ItemListView(ExtraContext, ListView):
    model = Item
    extra_context = {'active': ['_union_prod','__Item']}

    def get_queryset(self):
        queryset = super(ItemListView, self).get_queryset()
        item = self.request.GET.get('item')
        category = self.request.GET.get('category')
        supplier = self.request.GET.get('supplier')
        if item:
            queryset = queryset.filter(name__icontains=item)
        if category:
            queryset = queryset.filter(category__name__icontains=item)
        if supplier:
            queryset = queryset.filter(supplier__name__icontains=item)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context['form'] = ItemSearchForm
        return context

    def dispatch(self, *args, **kwargs):
        if self.request.GET.get('download'):
            return self.download_file()
        return super(ItemListView, self).dispatch(*args, **kwargs)

    def download_file(self, *args, **kwargs):

        _value = []
        columns = []
        item = self.request.GET.get('item')
        category = self.request.GET.get('category')
        supplier = self.request.GET.get('supplier')

        profile_choices = ['id', 'name', 'supplier__name', 'price', 'create_date']

        columns += [self.replaceMultiple(c, ['_', '__name'], ' ').title() for c in profile_choices]
        # Gather the Information Found
        # Create the HttpResponse object with Excel header.This tells browsers that
        # the document is a Excel file.
        response = HttpResponse(content_type='application/ms-excel')

        # The response also has additional Content-Disposition header, which contains
        # the name of the Excel file.
        response['Content-Disposition'] = 'attachment; filename=NyoweItems_%s.xls' % datetime.datetime.now().strftime(
            '%Y%m%d%H%M%S')

        # Create object for the Workbook which is under xlwt library.
        workbook = xlwt.Workbook()

        # By using Workbook object, add the sheet with the name of your choice.
        worksheet = workbook.add_sheet("Cooperatives")

        row_num = 0
        style_string = "font: bold on; borders: bottom dashed"
        style = xlwt.easyxf(style_string)

        for col_num in range(len(columns)):
            # For each cell in your Excel Sheet, call write function by passing row number,
            # column number and cell data.
            worksheet.write(row_num, col_num, columns[col_num], style=style)

        queryset = super(ItemListView, self).get_queryset().values(*profile_choices)
        if item:
            queryset = queryset.filter(name__icontains=item)
        if category:
            queryset = queryset.filter(category__name__icontains=item)
        if supplier:
            queryset = queryset.filter(supplier__name__icontains=item)

        for m in queryset:

            row_num += 1
            # ##print profile_choices
            row = [
                m['%s' % x] if 'create_date' not in x else m['%s' % x].strftime('%d-%m-%Y')  if m.get('%s' % x) else ""
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
    

def get_item_price(request, pk):
    try:
        pp = Item.objects.get(pk=pk)
        return JsonResponse({"price": pp.price})
    except Exception:
        return JsonResponse({"price": "error"})
    

    
    
