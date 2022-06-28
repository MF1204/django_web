from django.shortcuts import render
from django.views.generic import View
from django.http import HttpRequest, JsonResponse
from config.models import info_role, info_auth, info_menu, join_auth
from django.db import transaction
from django.forms.models import model_to_dict
import json
from django.shortcuts import redirect
from masterdata.views import serial


# ======== auth view ========
class auth(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        if request.session['auth'] != 1:
            print('접근제한')
            return redirect('/')
        context['rolelist'] = info_role.objects.filter(usage_flag=1)
        context['menulist'] = info_menu.objects.filter(usage_flag=1)
        context['authlist'] = info_auth.objects.filter(usage_flag=1)
        context['masterlist'] = join_auth.objects.filter(value=1)

        return render(request, 'masterdata/auth.html', context)

    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        context['success'] = True
        return JsonResponse(context, content_type='application/json')


class auth_select(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        role_id = data['role_id']
        selectrole = info_role.objects.get(id=role_id)
        role_name = selectrole.name
        masterauth = join_auth.objects.filter(role_id=selectrole).order_by('menu_id_id', 'auth_id_id')

        dictlist = []
        for one in masterauth:
            dictobj = {}
            dictone = model_to_dict(one)
            for key, val in dictone.items():
                if key == 'role_id':
                    role = info_role.objects.filter(id=val).first()
                    key = 'role'
                    val = role.name
                elif key == 'menu_id':
                    menu = info_menu.objects.filter(id=val).first()
                    key = 'menu'
                    val = menu.name
                elif key == 'auth_id':
                    auth = info_auth.objects.filter(id=val).first()
                    key = 'auth'
                    val = auth.name
                elif key == 'value':
                    key = 'value'
                dictobj.setdefault(key, val)
            dictlist.append(dictobj)

        context['role'] = list(dictlist)
        return JsonResponse(context, content_type='application/json')


class auth_update(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        print(data)
        idlist = data['idList']
        namelist = data['valList']
        print(idlist)
        print(namelist)
        for pkid, val in zip(idlist, namelist):
            try:
                with transaction.atomic():
                    auth = join_auth.objects.get(id=pkid)
                    auth.value = val
                    auth.save()
            except Exception as e:
                print('join_auth table update Error : ' + str(e))
                context['success'] = False
                context['message'] = "저장에 실패하였습니다."
                return JsonResponse(context, content_type='application/json')
        context['success'] = True
        context['message'] = '저장되었습니다.'
        return JsonResponse(context, content_type='application/json')


class menu_auto(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        menulist = info_menu.objects.all().order_by('id').values('id', 'name')
        context['menu'] = list(menulist)
        return JsonResponse(context, content_type='application/json')


# role 생성과 동시에 해당하는 권한이 생성되어야함
class role_create(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        rolename = data['role_name']
        flag = False
        for name in rolename:
            role = info_role.objects.all()
            if role.count() != 0:
                r_code = role.order_by('-id').first().code
                r_code = serial(r_code)
            else:
                r_code = 'R001'
            try:
                newrole = info_role.objects.create(code=r_code, usage_flag=1, name=name)
                flag = True
            except Exception as e:
                print('info_role table create Error : ' + str(e))
                context['success'] = False
                context['message'] = '등록에 실패했습니다.'
                return JsonResponse(context, content_type='application/json')
            if flag is True:
                menu_table = info_menu.objects.all()
                auth_table = info_auth.objects.all()
                for menu in menu_table:
                    for authobj in auth_table:
                        join = join_auth.objects.create(role_id=newrole, menu_id=menu, auth_id=authobj, value=0)

        context['success'] = True
        context['message'] = '등록되었습니다.'
        return JsonResponse(context, content_type='application/json')


class role_update(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        idlist = data['role_id']
        namelist = data['role_name']
        for roleid, name in zip(idlist, namelist):
            try:
                with transaction.atomic():
                    data = info_role.objects.get(id=roleid)
                    data.name = name
                    data.save()
            except Exception as e:
                print('info_role table update Error : ' + str(e))
                context['success'] = False
                context['message'] = "수정에 실패하였습니다."
                return JsonResponse(context, content_type='application/json')
        context['success'] = True
        context['message'] = '수정되었습니다.'
        return JsonResponse(context, content_type='application/json')


class role_delete(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        idlist = data['role_id']
        for roleid in idlist:
            try:
                with transaction.atomic():
                    data = info_role.objects.get(id=roleid)
                    data.usage_flag = 0
                    data.save()
            except Exception as e:
                print('info_role table delete Error : ' + str(e))
                context['success'] = False
                context['message'] = "삭제에 실패하였습니다."
                return JsonResponse(context, content_type='application/json')
        context['success'] = True
        context['message'] = '삭제되었습니다.'
        return JsonResponse(context, content_type='application/json')
