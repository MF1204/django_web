from django.shortcuts import render
from django.views.generic import View
from django.http import HttpRequest, JsonResponse
from config.models import info_department, info_process, info_equipment, info_chamber\
    , info_recipe, profile, User, join_auth
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import json
from django.shortcuts import redirect
from ..views import serial, makedirectory, versiondir, makepath, makestructure


# ======== process view ========
class Process(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        role = request.session['role']
        auth_list = join_auth.objects.filter(role_id_id=role['id'], menu_id_id=2, auth_id_id=1).values()
        auth_list = list(auth_list)
        value = auth_list[0]['value']

        if value != 1:
            print('접근제한')
            return redirect('/')

        user_id = request.user.id
        user = profile.objects.get(user_id=user_id)
        f_id = info_department.objects.get(id=user.department_id_id).headquarter_id.factory_id_id
        department_id = info_department.objects.filter(headquarter_id__factory_id=f_id)
        sendlist = info_process.objects.filter(department_id__in=department_id, usage_flag='1')

        context['process'] = sendlist
        return render(request, 'masterdata/process.html', context)


class process_select(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        flag = data['flag']
        foreign_id = data['foreign_id']
        sendlist = []
        if flag == '':
            user_id = request.user.id
            user = profile.objects.get(user_id=user_id)
            f_id = info_department.objects.get(id=user.department_id_id).headquarter_id.factory_id_id
            department_id = info_department.objects.filter(headquarter_id__factory_id=f_id)
            process = info_process.objects.filter(department_id__in=department_id, usage_flag='1').values()

            datas = []
            for one in process:
                print(one)
                print(one['department_id_id'])
                department_id = info_department.objects.get(id=one['department_id_id'])
                dictone = {
                    'id': one['id'],
                    'code': one['code'],
                    'name': one['name'],
                    'department_id': department_id.id,
                    'department_name': department_id.name,
                }
                # print(dictone)
                datas.append(dictone)
            sendlist = datas

        elif flag == 'process':
            equipment = info_equipment.objects.filter(process_id_id=foreign_id, usage_flag='1').values()
            datas = []
            for one in equipment:
                # print(one)
                profile_id = profile.objects.get(id=one['profile_id_id'])
                dictone = {
                    'id': one['id'],
                    'code': one['code'],
                    'name': one['name'],
                    'profile_id': profile_id.id,
                    'profile_name': profile_id.name,
                }
                # print(dictone)
                datas.append(dictone)
            sendlist = datas

        elif flag == 'equipment':
            sendchamber = info_chamber.objects.filter(equipment_id_id=foreign_id, usage_flag='1').values()
            sendlist = list(sendchamber.values())

        elif flag == 'chamber':
            datas = []
            try:
                recipe = info_recipe.objects.filter(chamber_id_id=foreign_id, usage_flag='1').values()
                for one in recipe:
                    # print(one)
                    profile_id = profile.objects.get(id=one['register_id'])
                    user_id = User.objects.get(id=profile_id.user_id)
                    dictone = {
                        'id': one['id'],
                        'code': one['code'],
                        'name': one['name'],
                        'revision': one['revision'],
                        'register_name': profile_id.name,
                        'register_phone': profile_id.phone,
                        'register_email': user_id.email,
                        'registdate': one['registdate'],
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


class depart_select(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        user_id = request.user.id
        user = profile.objects.get(user_id=user_id)
        # master_id = master.objects.get(user_id=user_id)
        # factory_id = master_id.factory_id
        f_id = info_department.objects.get(id=user.department_id_id).headquarter_id.factory_id_id
        department_id = info_department.objects.filter(headquarter_id__factory_id=f_id)
        sendlist = info_department.objects.filter(id__in=department_id, usage_flag='1').values()

        context['list'] = list(sendlist)
        return JsonResponse(context, content_type='application/json')


class profile_select(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        foreign_id = data['foreign_id']
        print(foreign_id)
        role = request.session['role']

        sendlist = profile.objects.filter(department_id_id=foreign_id, usage_flag='1').values()

        context['list'] = list(sendlist)
        return JsonResponse(context, content_type='application/json')


class insert_process(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        role = request.session['role']
        auth_list = join_auth.objects.filter(role_id_id=role['id'], menu_id_id=2, auth_id_id=2).values_list('value', flat=True)
        value = auth_list[0]
        if value != 1:
            print('접근제한')
            context['success'] = False
            context['message'] = '권한이 없습니다.'
            return JsonResponse(context, content_type='application/json')

        data = request.body.decode('utf-8')
        data = json.loads(data)
        info = data['flag']
        foreign_id = data['foreign_id']
        namelist = data['list']
        flag = ''       # 작업한 id가 어느테이블 소속인지
        if info == 'process':
            for name in namelist:
                process = info_process.objects.all()
                if process.count() != 0:
                    p_code = process.order_by('-id').first().code
                    p_code = serial(p_code)
                else:
                    p_code = 'P001'
                try:
                    process = info_process.objects.create(code=p_code, usage_flag='1', name=name['name'], department_id_id=name['select'])
                    flag = ''
                    makedirectory(process.code)

                except Exception as e:
                    print('info_process table create Error : ' + str(e))
                    context['success'] = False
                    context['message'] = '등록에 실패했습니다.'
                    return JsonResponse(context, content_type='application/json')

        elif info == 'equipment':
            try:
                p_id = info_process.objects.get(id=foreign_id)
            except ObjectDoesNotExist as e:
                print('info_process table id Error : ' + str(e))
                context['success'] = False
                context['message'] = '등록에 실패했습니다.'
                return JsonResponse(context, content_type='application/json')
            for name in namelist:
                equipment = info_equipment.objects.all()
                if equipment.count() != 0:
                    e_code = equipment.order_by('-id').first().code
                    e_code = serial(e_code)
                else:
                    e_code = 'E001'
                try:
                    equipment = info_equipment.objects.create(process_id=p_id, code=e_code, usage_flag='1', name=name['name'], profile_id_id=name['select'])
                    flag = 'process'
                    makedirectory(equipment.process_id.code, equipment.code)
                except Exception as e:
                    print('info_equipment table create Error : ' + str(e))
                    context['success'] = False
                    context['message'] = '등록에 실패했습니다.'
                    return JsonResponse(context, content_type='application/json')

        elif info == 'chamber':
            try:
                e_id = info_equipment.objects.get(id=foreign_id)
            except ObjectDoesNotExist as e:
                print('info_equipment table id Error : ' + str(e))
                context['success'] = False
                context['message'] = '등록에 실패했습니다.'
                return JsonResponse(context, content_type='application/json')
            for name in namelist:
                chamber = info_chamber.objects.all()
                if chamber.count() != 0:
                    c_code = chamber.order_by('-id').first().code
                    c_code = serial(c_code)
                else:
                    c_code = 'C001'
                try:
                    chamber = info_chamber.objects.create(equipment_id=e_id, code=c_code, usage_flag='1', name=name)
                    flag = 'equipment'
                    makedirectory(chamber.equipment_id.process_id.code, chamber.equipment_id.code, chamber.code)
                except Exception as e:
                    print('info_chamber table create Error : ' + str(e))
                    context['success'] = False
                    context['message'] = '등록에 실패했습니다.'
                    return JsonResponse(context, content_type='application/json')

        elif info == 'recipe':
            try:
                c_id = info_chamber.objects.get(id=foreign_id)
            except ObjectDoesNotExist as e:
                print('info_chamber table id Error : ' + str(e))
                context['success'] = False
                context['message'] = '등록에 실패했습니다.'
                return JsonResponse(context, content_type='application/json')
            for one in namelist:
                name = one['name']
                revision = one['revision']
                p_id = one['profile']
                print(name, revision, profile)
                try:
                    profile_id = profile.objects.get(id=p_id)
                except ObjectDoesNotExist as e:
                    print('profile table id Error : ' + str(e))
                    context['success'] = False
                    context['message'] = '등록에 실패했습니다.'
                    return JsonResponse(context, content_type='application/json')

                recipe_code = info_recipe.objects.filter(chamber_id=c_id, name=name).values_list('code', flat=True)
                if len(recipe_code) == 0:
                    recipe = info_recipe.objects.all()
                    if recipe.count() != 0:
                        r_code = recipe.order_by('-id').first().code
                        r_code = serial(r_code)
                    else:
                        r_code = 'R001'
                else:
                    r_code = recipe_code[0]

                try:
                    recipe = info_recipe.objects.create(chamber_id=c_id, code=r_code, usage_flag='1', name=name, revision=revision, register=profile_id)
                    flag = 'chamber'
                    makestructure(recipe.chamber_id.equipment_id.process_id.code, recipe.chamber_id.equipment_id.code, recipe.chamber_id.code, recipe.code)
                    versiondir(recipe.chamber_id.equipment_id.process_id.code, recipe.chamber_id.equipment_id.code, recipe.chamber_id.code, recipe.code, revision=revision)
                except Exception as e:
                    print('info_recipe table create Error : ' + str(e))
                    context['success'] = False
                    context['message'] = '등록에 실패했습니다.'
                    return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['flag'] = flag
        return JsonResponse(context, content_type='application/json')


class update_process(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        role = request.session['role']
        auth_list = join_auth.objects.filter(role_id_id=role['id'], menu_id_id=2, auth_id_id=2).values_list('value', flat=True)
        value = auth_list[0]
        if value != 1:
            print('접근제한')
            context['success'] = False
            context['message'] = '권한이 없습니다.'
            return JsonResponse(context, content_type='application/json')

        data = request.body.decode('utf-8')
        data = json.loads(data)
        info = data['flag']
        updatelist = data['list']
        if info == 'process':
            for one in updatelist:
                pid = one['id']
                pname = one['name']
                did = one['foreign_id']
                try:
                    with transaction.atomic():
                        data = info_process.objects.get(id=pid)
                        data.name = pname
                        data.department_id_id = did
                        data.save()
                except Exception as e:
                    print('info_process table update Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "수정에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')
        elif info == 'equipment':
            for one in updatelist:
                eid = one['id']
                ename = one['name']
                pid = one['foreign_id']
                try:
                    with transaction.atomic():
                        data = info_equipment.objects.get(id=eid)
                        data.name = ename
                        data.profile_id_id=pid
                        data.save()
                except Exception as e:
                    print('info_equipment table update Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "수정에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        elif info == 'chamber':
            for one in updatelist:
                cid = one['id']
                cname = one['name']
                try:
                    with transaction.atomic():
                        data = info_chamber.objects.get(id=cid)
                        data.name = cname
                        data.save()
                except Exception as e:
                    print('info_chamber table update Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "수정에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        elif info == 'recipe':
            user_id = request.user.id
            user = profile.objects.get(user_id=user_id)
            d_id = user.department_id_id
            recipe_id = updatelist[0]['id']
            re_department = info_recipe.objects.get(id=recipe_id).chamber_id.equipment_id.process_id.department_id_id
            if d_id != re_department :
                print('제한된 행위 탐지')
                context['success'] = False
                context['message'] = '담당팀 소속만 편집가능합니다.'
                return JsonResponse(context, content_type='application/json')
            for one in updatelist:
                rid = one['id']
                rname = one['name']
                revision = one['revision']
                profile_id = one['foreign_id']
                try:
                    with transaction.atomic():
                        data = info_recipe.objects.get(id=rid)
                        data.name = rname
                        data.revision = revision
                        data.register_id = profile_id
                        data.save()
                except Exception as e:
                    print('info_recipe table update Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "수정에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        context['success'] = True
        return JsonResponse(context, content_type='application/json')


class delete_process(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        # role = request.session['role']
        data = request.body.decode('utf-8')
        data = json.loads(data)
        info = data['flag']
        deletelist = data['list']
        if info == 'process':
            for one in deletelist:
                try:
                    with transaction.atomic():
                        data = info_process.objects.get(id=one)
                        data.usage_flag = 0
                        data.save()
                except Exception as e:
                    print('info_process table delete Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "삭제에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        elif info == 'equipment':
            for one in deletelist:
                try:
                    with transaction.atomic():
                        data = info_equipment.objects.get(id=one)
                        data.usage_flag = 0
                        data.save()
                except Exception as e:
                    print('info_equipment table delete Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "삭제에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        elif info == 'chamber':
            for one in deletelist:
                try:
                    with transaction.atomic():
                        data = info_chamber.objects.get(id=one)
                        data.usage_flag = 0
                        data.save()
                except Exception as e:
                    print('info_chamber table delete Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "삭제에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')
        elif info == 'recipe':
            for one in deletelist:
                try:
                    with transaction.atomic():
                        data = info_recipe.objects.get(id=one)
                        data.usage_flag = 0
                        data.save()
                except Exception as e:
                    print('info_recipe table update Error : ' + str(e))
                    context['success'] = False
                    context['message'] = "삭제에 실패하였습니다."
                    return JsonResponse(context, content_type='application/json')

        context['success'] = True
        return JsonResponse(context, content_type='application/json')
# ============================
