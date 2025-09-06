# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.urls import path
from apps.dyn_api import views
from apps.dyn_api.views_frontend_logs import (
    FrontendLogsAPIView, frontend_stats_api, user_activity_timeline
)

urlpatterns = [
    path('api/', views.index, name="dynamic_api"),

    # APIs dinámicas originales
    path('api/<str:model_name>/'          , views.DynamicAPI.as_view(), name="model_api"),
    path('api/<str:model_name>/<str:id>'  , views.DynamicAPI.as_view()),
    path('api/<str:model_name>/<str:id>/' , views.DynamicAPI.as_view()),
    
    # APIs de logging y auditoría
    path('api/frontend-logs/', FrontendLogsAPIView.as_view(), name="frontend_logs_api"),
    path('api/frontend-stats/', frontend_stats_api, name="frontend_stats_api"),
    path('api/user-activity-timeline/', user_activity_timeline, name="user_activity_timeline"),
]
