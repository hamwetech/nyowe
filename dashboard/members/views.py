# coding=utf-8
from __future__ import division

import datetime

from rest_framework.decorators import action
from rest_framework import status
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from django.views.generic import TemplateView
from dashboard.members import queries
from dashboard.members.utils import execute_sql


class MemberAnalyticalDashboard(TemplateView):
    template_name = "member_analytical_dashboard.html"


class DashBoardViewSet(viewsets.ModelViewSet):
    renderer_classes = (JSONRenderer,)
    model = None
    response = {'details': 'Access Denied'}
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    def destroy(self, request, *args, **kwargs):
        return Response(self.response, status=status.HTTP_200_OK, headers={})

    def retrieve(self, request, *args, **kwargs):
        return Response(self.response, status=status.HTTP_200_OK, headers={})

    def update(self, request, *args, **kwargs):
        return Response(self.response, status=status.HTTP_200_OK, headers={})

    def create(self, request, *args, **kwargs):
        return Response(self.response, status=status.HTTP_200_OK, headers={})

    def list(self, request, *args, **kwargs):
        return Response(self.response, status=status.HTTP_200_OK, headers={})

    @staticmethod
    def dataFilters(request):
        txn_year = datetime.date.today().year
        # year, default to the current year if none.
        try:
            _year = request.query_params.get("year") if request.query_params.get("year") else txn_year
        except TypeError:
            _year = txn_year

        # region
        try:
            _region = request.query_params.get("region") if request.query_params.get("region") else None
        except TypeError:
            _region = None

        # district
        try:
            _district = request.query_params.get("district") if request.query_params.get("district") else None
        except TypeError:
            _district = None

        return _year, _region, _district

    @action(detail=False, methods=['get'], url_path='members-overview')
    def totalMembers(self, request, *args, **kwargs):
        _year, _region, _district = DashBoardViewSet.dataFilters(request)

        # construct query where clause
        query_clause = 'WHERE year_created={} '.format(_year)
        if _region:
            query_clause += 'region_id={} '.format(_region)
        if _district:
            query_clause += 'district_id={} '.format(_district)

        # execute query and return that to client.
        query_results = execute_sql(queries.member.format(query_clause))

        # Initialize dictionaries to hold counts for each gender
        female_counts = {i: 0 for i in range(0, 13)}
        male_counts = {i: 0 for i in range(0, 13)}

        # set data names
        female_counts[0] = "Female"
        male_counts[0] = "Male"

        # Populate counts for each gender and month
        for item in query_results:
            if item['gender'] == 'Female':
                female_counts[item['month_created']] += item['member_count']
            elif item['gender'] == 'Male':
                male_counts[item['month_created']] += item['member_count']

        # Convert counts to lists based on legend order
        female_list = [female_counts[i] for i in range(0, 13)]
        male_list = [male_counts[i] for i in range(0, 13)]

        # Define legend
        legend = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

        # Assemble the result
        result = {'legend': legend, 'female': female_list, 'male': male_list}
        return Response(result, status=status.HTTP_200_OK, headers={})

    @action(detail=False, methods=['get'], url_path='collections-overview')
    def totalCollections(self, request, *args, **kwargs):
        _year, _region, _district = DashBoardViewSet.dataFilters(request)

        # construct query where clause
        query_clause = 'WHERE collection_year={} '.format(_year)
        if _region:
            query_clause += 'region_id={} '.format(_region)
        if _district:
            query_clause += 'district_id={} '.format(_district)

        # execute query and return that to client.
        query_results = execute_sql(queries.collection.format(query_clause))

        # Initialize dictionaries to hold Weights for each Amounts
        weights_sum = {i: 0 for i in range(0, 13)}
        amount_sum = {i: 0 for i in range(0, 13)}

        # set data names
        weights_sum[0] = "Weight"
        amount_sum[0] = "Amounts"

        # Populate counts for each Weight and Amounts
        for item in query_results:
            weights_sum[item['collection_month']] += item['weights_sum']
            amount_sum[item['collection_month']] += item['amount_sum']

        # Convert counts to lists based on legend order
        weights_list = [weights_sum[i] for i in range(0, 13)]
        amount_list = [amount_sum[i] for i in range(0, 13)]

        # Define legend
        legend = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

        # Assemble the result
        result = {'legend': legend, 'weight': weights_list, 'amounts': amount_list}

        return Response(result, status=status.HTTP_200_OK, headers={})

    @action(detail=False, methods=['get'], url_path='orders-overview')
    def totalOrders(self, request, *args, **kwargs):
        _year, _region, _district = DashBoardViewSet.dataFilters(request)

        # construct query where clause
        query_clause = 'WHERE year_created={} '.format(_year)
        if _region:
            query_clause += 'region_id={} '.format(_region)
        if _district:
            query_clause += 'district_id={} '.format(_district)

        # execute query and return that to client.
        query_results = execute_sql(queries.orders.format(query_clause))

        response = {
            'members': query_results,
        }
        return Response(response, status=status.HTTP_200_OK, headers={})
