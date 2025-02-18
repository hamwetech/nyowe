from django.conf.urls import url

from activity.views.training import *

urlpatterns = [
    url(r'thamatic/list/$', ThematicAreaListView.as_view(), name='thematic_list'),
    url(r'thamatic/create/$',  ThematicAreaCreateView.as_view(), name='thamatic_create'),
    url(r'thamatic/(?P<pk>[\w]+)/$', ThematicAreaUpdateView.as_view(), name='thamatic_edit'),
    url(r'training/session/(?P<pk>[\w]+)/$', TrainingSessionDetailView.as_view(), name='detail_list'),
    url(r'training/session/$', TrainingSessionListView.as_view(), name='training_list'),
    url(r'training/create/$', TrainingCreateView.as_view(), name='training_create'),
    url(r'training/upload/$', UploadTrainingSessionView.as_view(), name='training_upload'),
    url(r'external/create/$', ExternalTrainerCreateView.as_view(), name='external_create'),

    url(r'meeting/list/$', MeetingListView.as_view(), name='meeting_list'),
    url(r'meeting/create/$', MeetingCreateView.as_view(), name='meeting_create'),
    url(r'meeting/update/(?P<pk>[\w]+)/$', MeetingUpdateView.as_view(), name='meeting_update'),
    url(r'meeting/detail/(?P<pk>[\w]+)/$', MeetingDetailView.as_view(), name='meeting_detail')
]