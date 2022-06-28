from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.contrib.auth.models import User
from django.db import transaction
from django.forms.models import model_to_dict
from config.models import profile, info_factory, info_headquarter, info_department, info_process, join_auth
import json
from django.contrib.auth.mixins import LoginRequiredMixin


class LoginView(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}
        if request.user.id:
            return redirect('/')

        return render(request, 'login.html', context)

    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        id = request.POST['card-id']
        password = request.POST['card-password']
        user = authenticate(request, username=id, password=password)

        if user is not None:
            login(request, user)
            request.session['user'] = id
            user = request.user.id
            role_id = profile.objects.get(user_id=user).role_id
            role = model_to_dict(role_id)
            request.session['role'] = role

            # 권한관리 header에서 제어
            auth_list = join_auth.objects.filter(role_id_id=role['id'], menu_id_id=3, auth_id_id=1).values()
            auth_list = list(auth_list)
            request.session['auth'] = auth_list[0]['value']

            context['success'] = True
            context['message'] = '로그인 되었습니다.'
        else:
            context['success'] = False
            context['message'] = '일치하는 회원정보가 없습니다.'
        return JsonResponse(context, content_type='application/json')


class LogoutPageView(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        return render(request, 'logout.html', context)


class RegisterView(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        userid = request.POST.get('card-id')
        password = userid
        email = request.POST['card-email']
        name = request.POST['card-name']
        phone = request.POST['card-phone']
        factory = request.POST['card-factory']
        department = request.POST['card-depart']
        auth = request.POST['card-auth']

        try:
            user = User.objects.get(username=userid)
            context['success'] = False
            context['message'] = '아이디가 이미 존재합니다.'
            return JsonResponse(context, content_type='application/json')

        except:
            user = User.objects.create_user(
                username=userid,
                email=email,
                password=password
            )
            user_id = user.id
            rsProfile = profile.objects.get(user_id=user_id)
            rsProfile.name = name
            rsProfile.phone = phone
            rsProfile.factory = factory
            rsProfile.department = department
            rsProfile.auth = auth
            rsProfile.save()

        context['success'] = True
        context['message'] = '등록 되었습니다.'
        return JsonResponse(context, content_type='application/json')


class index(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}
        return render(request, '../templates/index.html', context)


class EmployeeView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}
        context['username'] = request.user.username

        context['user'] = User.objects.all()
        context['profile'] = profile.objects.all()
        context['factory'] = info_factory.objects.all()
        context['department'] = info_department.objects.all()
        context['headquarter'] = info_headquarter.objects.all()

        return render(request, 'employee.html', context)

    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        userid = request.POST.get('card-id')
        password = userid
        email = request.POST['card-email']
        name = request.POST['card-name']
        phone = request.POST['card-phone']
        factory = request.POST['card-factory']
        department = request.POST['card-depart']
        auth = request.POST['card-auth']

        try:
            user = User.objects.get(username=userid)
            context['success'] = False
            context['message'] = '아이디가 이미 존재합니다.'
            return JsonResponse(context, content_type='application/json')

        except:
            user = User.objects.create_user(
                username=userid,
                email=email,
                password=password
            )
            user_id = user.id
            rsProfile = profile.objects.get(user_id=user_id)
            rsProfile.name = name
            rsProfile.phone = phone
            rsProfile.factory = factory
            rsProfile.department = department
            rsProfile.auth = auth
            rsProfile.save()

        context['success'] = True
        context['message'] = '등록 되었습니다.'
        return JsonResponse(context, content_type='application/json')


class update_employee(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        username = request.POST['eno']

        try:
            with transaction.atomic():
                userid = User.objects.get(username=username).id
                emp = profile.objects.get(user_id=userid)
                depart = info_department.objects.get(code=request.POST['depart'])

                emp.department_id = depart
                emp.save()
        except:
            context['success'] = False
            context['message'] = "수정에 실패하였습니다."
            return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['message'] = "수정되었습니다."

        return JsonResponse(context, content_type='application/json')


class ProfileView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}
        context['username'] = request.user.username

        user = User.objects.get(id=request.user.id)
        info_profile = profile.objects.get(user_id=user)

        context['user'] = user
        context['profile'] = info_profile

        return render(request, 'profile.html', context)


class hq_select(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        data = request.body.decode('utf-8')
        data = json.loads(data)
        code = data['code']

        try:
            factory_id = info_factory.objects.get(code=code)
        except:
            context['success'] = False
            context['headquarter'] = []
            context['department'] = []
            return JsonResponse(context, content_type='application/json')

        hq = info_headquarter.objects.filter(factory_id=factory_id).values('code', 'name')

        context['headquarter'] = list(hq.values())
        context['success'] = True
        return JsonResponse(context, content_type='application/json')


class process_select(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        data = request.body.decode('utf-8')
        data = json.loads(data)
        code = data['code']

        try:
            factory_id = info_factory.objects.get(code=code)
        except:
            context['success'] = False
            context['headquarter'] = []
            context['department'] = []
            return JsonResponse(context, content_type='application/json')

        process = info_process.objects.filter(factory_id=factory_id).values('code', 'name')

        context['process'] = list(process.values())
        context['success'] = True
        return JsonResponse(context, content_type='application/json')


class depart_select(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        data = request.body.decode('utf-8')
        data = json.loads(data)
        code = data['code']
        if data['search'] == 'process':
            try:
                process_id = info_process.objects.get(code=code)
            except:
                context['success'] = False
                context['department'] = []
                return JsonResponse(context, content_type='application/json')

            depart = info_department.objects.filter(process_id_id=process_id).values('code', 'name')

        else:
            try:
                headquarter_id = info_headquarter.objects.get(code=code)
            except:
                context['success'] = False
                context['department'] = []
                return JsonResponse(context, content_type='application/json')

            depart = info_department.objects.filter(headquarter_id_id=headquarter_id).values('code', 'name')

        context['department'] = list(depart.values())
        context['success'] = True
        return JsonResponse(context, content_type='application/json')
