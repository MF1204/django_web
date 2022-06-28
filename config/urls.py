"""config URL Configuration

The `urlpatterns` list routes URLs to anomaly_views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function anomaly_views
    1. Add an import:  from my_app import anomaly_views
    2. Add a URL to urlpatterns:  path('', anomaly_views.home, name='home')
Class-based anomaly_views
    1. Add an import:  from other_app.anomaly_views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import *
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index.as_view()),
    path('anomaly/', include('anomaly.urls')),
    # path('condition/', include('condition.urls')),
    # path('discrepancy/', include('discrepancy.urls')),
    # path('vision/', include('vision.urls')),
    # path('tracking/', include('tracking.urls')),
    path('', include('masterdata.urls')),

    # 직원정보
    path('login', LoginView.as_view(), name='login'),
    path('logout-page', LogoutPageView.as_view(), name='logout-page'),
    path('logout', LogoutView.as_view(next_page='/logout-page'), name='logout'),
    path('employee/', EmployeeView.as_view(), name='employee'),
    path('employee/update', update_employee.as_view(), name='employee_update'),
    path('employee/hq_select/', hq_select.as_view(), name='hq_select'),
    path('employee/process_select/', process_select.as_view(), name='process_select'),
    path('employee/depart_select/', depart_select.as_view(), name='depart_select'),
    path('profile', ProfileView.as_view(), name='profile'),
]
