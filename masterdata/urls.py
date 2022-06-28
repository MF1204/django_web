from django.urls import path
from .masterview import groupview, processview, authview
from . import views

app_name = 'masterdata'

urlpatterns = [
    # process
    path('master/process/', processview.Process.as_view(), name='process'),
    path('master/process_select/', processview.process_select.as_view(), name='process_select'),
    path('master/depart_select/', processview.depart_select.as_view(), name='depart_select'),
    path('master/profile_select/', processview.profile_select.as_view(), name='profile_select'),
    path('master/insert_process/', processview.insert_process.as_view(), name='insert_process'),
    path('master/update_process/', processview.update_process.as_view(), name='update_process'),
    path('master/delete_process/', processview.delete_process.as_view(), name='delete_process'),
    # group
    path('master/group', groupview.group.as_view(), name='group'),
    path('master/group_select/', groupview.group_select.as_view(), name='group_select'),
    path('master/role_select/', groupview.role_select.as_view(), name='role_select'),
    path('master/insert_info/', groupview.insert_info.as_view(), name='insert_info'),
    path('master/update_info/', groupview.update_info.as_view(), name='update_info'),
    path('master/delete_info/', groupview.delete_info.as_view(), name='delete_info'),
    # auth
    path('master/auth/', authview.auth.as_view(), name='auth'),
    path('master/auth_select/', authview.auth_select.as_view(), name='auth_select'),
    path('master/auth_update/', authview.auth_update.as_view(), name='auth_update'),
    path('master/menu_auto/', authview.menu_auto.as_view(), name='menu_auto'),
    path('master/role_create/', authview.role_create.as_view(), name='role_create'),
    path('master/role_update/', authview.role_update.as_view(), name='role_update'),
    path('master/role_delete/', authview.role_delete.as_view(), name='role_delete'),
]