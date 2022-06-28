from django.shortcuts import render
from django.views.generic import View
from django.http import HttpRequest, JsonResponse
from config.models import info_factory, info_headquarter, info_department,\
    profile, User, info_role, join_auth
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import json
from django.shortcuts import redirect
from ..views import serial, username


# ======== group view ========
class group(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}
        role = request.session['role']
        auth_list = join_auth.objects.filter(role_id_id=role['id'], menu_id_id=1, auth_id_id=1).values()
        auth_list = list(auth_list)
        value = auth_list[0]['value']

        if value != 1:
            print('접근제한')
            return redirect('/')

        factory = info_factory.objects.filter(usage_flag='1')

        context['factory'] = factory
        return render(request, 'masterdata/group.html', context)


class group_select(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        flag = data['flag']
        foreign_id = data['foreign_id']
        sendlist = []
        if flag == '':
            sendfac = info_factory.objects.filter(usage_flag='1').values()
            sendlist = list(sendfac.values())

        elif flag == 'factory':
            sendhq = info_headquarter.objects.filter(factory_id_id=foreign_id, usage_flag='1').values()
            sendlist = list(sendhq.values())

        elif flag == 'hq':
            sendteam = info_department.objects.filter(headquarter_id_id=foreign_id, usage_flag='1').values()
            sendlist = list(sendteam.values())

        elif flag == 'depart':
            datas = []
            try:
                people = profile.objects.filter(department_id_id=foreign_id, usage_flag='1').values()
                for person in people:
                    # print(person)
                    user_id = User.objects.get(id=person['user_id'])
                    department_id = info_department.objects.get(id=person['department_id_id'])
                    role_id = info_role.objects.get(id=person['role_id_id'])
                    dictone = {
                        'id': person['id'],
                        'username': user_id.username,
                        'name': person['name'],
                        'email': user_id.email,
                        'phone': person['phone'],
                        'role': role_id.name
                    }
                    # print(dictone)
                    datas.append(dictone)
                sendlist = datas
            except Exception as e:
                sendlist = ''
                print(e)
                context['success'] = False
                return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['list'] = sendlist
        return JsonResponse(context, content_type='application/json')


class role_select(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}
        sendlist = info_role.objects.all().values()
        context['list'] = list(sendlist)
        return JsonResponse(context, content_type='application/json')


class insert_info(View):
    def post(self, request: HttpRequest, *args, **kwargs):

        role = request.session['role']
        auth_list = join_auth.objects.filter(role_id_id=role['id'], menu_id_id=1, auth_id_id=1).values()
        auth_list = list(auth_list)
        value = auth_list[0]['value']

        if value != 1:
            print('접근제한')
            return redirect('/')

        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        info = data['flag']
        foreign_id = data['foreign_id']
        namelist = data['list']
        flag = ''       # 작업한 id가 어느테이블 소속인지
        if info == 'factory':
            for name in namelist:
                factory = info_factory.objects.all()
                if factory.count() != 0:
                    f_code = factory.order_by('-id').first().code
                    f_code = serial(f_code)
                else:
                    f_code = 'F001'
                try:
                    factory = info_factory.objects.create(code=f_code, usage_flag='1', name=name)
                    flag = ''
                except Exception as e:
                    print('info_factory table create Error : ' + str(e))
                    context['success'] = False
                    context['message'] = '등록에 실패했습니다.'
                    return JsonResponse(context, content_type='application/json')

        elif info == 'hq':
            try:
                f_id = info_factory.objects.get(id=foreign_id)
            except ObjectDoesNotExist as e:
                print('info_factory table id Error : ' + str(e))
                context['success'] = False
                context['message'] = '등록에 실패했습니다.'
                return JsonResponse(context, content_type='application/json')

            for name in namelist:
                hq = info_headquarter.objects.all()
                if hq.count() != 0:
                    h_code = hq.order_by('-id').first().code
                    h_code = serial(h_code)
                else:
                    h_code = 'H001'
                try:
                    headquarter = info_headquarter.objects.create(factory_id=f_id, code=h_code, usage_flag='1', name=name)
                    flag = 'factory'
                except Exception as e:
                    print('info_headquarter table create Error : ' + str(e))
                    context['success'] = False
                    context['message'] = '등록에 실패했습니다.'
                    return JsonResponse(context, content_type='application/json')

        elif info == 'depart':
            try:
                h_id = info_headquarter.objects.get(id=foreign_id)
                f_id = h_id.factory_id
            except ObjectDoesNotExist as e:
                print('info_headquarter table id Error : ' + str(e))
                context['success'] = False
                context['message'] = '등록에 실패했습니다.'
                return JsonResponse(context, content_type='application/json')
            for name in namelist:
                depart = info_department.objects.all()
                if depart.count() != 0:
                    d_code = depart.order_by('-id').first().code
                    d_code = serial(d_code)
                else:
                    d_code = 'D001'
                try:
                    department = info_department.objects.create(headquarter_id=h_id, code=d_code, usage_flag='1', name=name)
                    flag = 'hq'
                except Exception as e:
                    print('info_department table create Error : ' + str(e))
                    context['success'] = False
                    context['message'] = '등록에 실패했습니다.'
                    return JsonResponse(context, content_type='application/json')

        elif info == 'person':
            try:
                d_id = info_department.objects.get(id=foreign_id)
            except ObjectDoesNotExist as e:
                print('info_department table id Error : ' + str(e))
                context['success'] = False
                context['message'] = '등록에 실패했습니다.'
                return JsonResponse(context, content_type='application/json')
            for adduser in namelist:
                name = adduser['name']
                email = adduser['email']
                phone = adduser['phone']
                role = adduser['role']
                print(name, email, phone, role)
                try:
                    a_id = info_role.objects.get(id=role)
                except ObjectDoesNotExist as e:
                    print('info_role table id Error : ' + str(e))
                    context['success'] = False
                    context['message'] = '등록에 실패했습니다.'
                    return JsonResponse(context, content_type='application/json')
                user_profile = User.objects.all()
                if user_profile.count() != 0:
                    u_code = user_profile.order_by('-id').first().username
                    u_code = username(u_code)
                else:
                    u_code = username('0')
                try:
                    user = User.objects.get(username=u_code)
                    context['success'] = False
                    context['message'] = '이미 존재하는 사번입니다.'
                    return JsonResponse(context, content_type='application/json')
                except ObjectDoesNotExist as e:
                    user = User.objects.create_user(
                        username=u_code,
                        email=email,
                        password=u_code
                    )
                    user_id = user.id
                    rsProfile = profile.objects.get(user_id=user_id)
                    rsProfile.department_id = d_id
                    rsProfile.name = name
                    rsProfile.phone = phone
                    rsProfile.auth_id = a_id
                    rsProfile.save()

                    flag = 'depart'

        context['success'] = True
        context['flag'] = flag
        return JsonResponse(context, content_type='application/json')


class update_info(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        info = data['flag']
        updatelist = data['list']
        if info == 'factory':
            for one in updatelist:
                fid = one['id']
                fname = one['name']
                try:
                    with transaction.atomic():
                        data = info_factory.objects.get(id=fid)
                        data.name = fname
                        data.save()
                except Exception as e:
                    print('info_factory table update Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "수정에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')
        elif info == 'hq':
            for one in updatelist:
                hid = one['id']
                hname = one['name']
                try:
                    with transaction.atomic():
                        data = info_headquarter.objects.get(id=hid)
                        data.name = hname
                        data.save()
                except Exception as e:
                    print('info_headquarter table update Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "수정에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        elif info == 'depart':
            for one in updatelist:
                did = one['id']
                dname = one['name']
                try:
                    with transaction.atomic():
                        data = info_department.objects.get(id=did)
                        data.name = dname
                        data.save()
                except Exception as e:
                    print('info_department table update Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "수정에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        elif info == 'person':
            for one in updatelist:
                pid = one['id']
                pname = one['name']
                pemail = one['email']
                pphone = one['phone']
                arole = info_role.objects.get(id=one['role'])
                try:
                    with transaction.atomic():
                        data = profile.objects.get(id=pid)
                        data.name = pname
                        data.phone = pphone
                        data.auth_id = arole
                        data.save()
                        user = User.objects.get(id=data.user_id)
                        user.email = pemail
                        user.save()
                except Exception as e:
                    print('info_department table update Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "수정에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        context['success'] = True
        return JsonResponse(context, content_type='application/json')


class delete_info(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        info = data['flag']
        deletelist = data['list']
        if info == 'factory':
            for one in deletelist:
                try:
                    with transaction.atomic():
                        data = info_factory.objects.get(id=one)
                        data.usage_flag = 0
                        data.save()
                except Exception as e:
                    print('info_factory table delete Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "삭제에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        elif info == 'headquarter':
            for one in deletelist:
                try:
                    with transaction.atomic():
                        data = info_headquarter.objects.get(id=one)
                        data.usage_flag = 0
                        data.save()
                except Exception as e:
                    print('info_headquarter table delete Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "삭제에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        elif info == 'depart':
            for one in deletelist:
                try:
                    with transaction.atomic():
                        data = info_department.objects.get(id=one)
                        data.usage_flag = 0
                        data.save()
                except Exception as e:
                    print('info_department table delete Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "삭제에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')
        elif info == 'person':
            for one in deletelist:
                try:
                    with transaction.atomic():
                        data = profile.objects.get(id=one)
                        data.usage_flag = 0
                        data.save()
                        user = User.objects.get(id=data.user_id)
                        user.is_active = 0
                        user.save()
                except Exception as e:
                    print('user_profile table update Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "삭제에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        context['success'] = True
        return JsonResponse(context, content_type='application/json')
# ============================
