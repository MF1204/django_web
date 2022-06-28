from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from config.models import mmModel, mmDataset, mmRecipe, mhMonitoring
# from aiengine.monitoring_excute import Target
from django.core.files.storage import FileSystemStorage
from django.db import transaction
import traceback
from django.shortcuts import render, redirect, get_object_or_404
import os
import csv
import datetime
import pandas
import json
import time

monitoring = None


class monitoringmain(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        equip_sql = '''
            SELECT id, equip_name FROM mm_dataset WHERE purpose='TRN' GROUP BY equip_name 
        '''

        context = {
            'equip_select': mmModel.objects.raw(equip_sql)
        }

        return render(request, 'monitoringmain.html', context)


class find_chamber(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        rsData = json.loads(request.body.decode("utf-8"))
        equip_name = rsData['equip_name']
        data = mmDataset.objects.filter(equip_name=equip_name, purpose="TRN").values_list('chamber_name', flat=True).distinct()

        context = {
            'chamber_list': list(data)
        }

        return JsonResponse(context, content_type='application/json')


class find_recipe(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        rsData = json.loads(request.body.decode("utf-8"))
        chamber_name = rsData['chamber_name']
        data = mmDataset.objects.filter(chamber_name=chamber_name, purpose="TRN").values_list('recipe_name', flat=True).distinct()

        context = {
            'recipe_list': list(data)
        }

        return JsonResponse(context, content_type='application/json')


class find_revision(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        rsData = json.loads(request.body.decode("utf-8"))
        recipe_name = rsData['recipe_name']
        data = mmDataset.objects.filter(recipe_name=recipe_name, purpose="TRN").values_list('revision_no', flat=True).distinct()

        context = {
            'revision_list': list(data)
        }

        return JsonResponse(context, content_type='application/json')


class find_sensor(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        rsData = json.loads(request.body.decode("utf-8"))
        equip_name = rsData['equip_name']
        chamber_name = rsData['chamber_name']
        recipe_name = rsData['recipe_name']
        revision_no = rsData['revision_no']
        data = mmRecipe.objects.filter(equip_name=equip_name, chamber_name=chamber_name, recipe_name=recipe_name, revision_no=revision_no)

        context = {
            'sensor_list': list(data.values())
        }

        return JsonResponse(context, content_type='application/json')


class run_monitoring(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        global monitoring   #global 변수로 선언하여 센서 재선택시 기존 thread가 중단되도록 설정
        context = {}

        #기존 thread가 존재하는 경우 기존 thread 중단
        if monitoring != None :
            monitoring.run_stop()

        rootpath = os.getcwd()
        sep = os.sep
        #모니터링 후 에러 파일 저장 디렉토리
        anomalies_path = rootpath + f"{sep}static{sep}data{sep}monitoring_anomalies" + sep
        print(anomalies_path)

        #모니터링을 진행할 파일 업로드 경로
        monitoring_path = rootpath + f'{sep}static{sep}data{sep}user'
        print(monitoring_path)

        rsData = json.loads(request.body.decode("utf-8"))
        equip_name = rsData['equip_name']
        chamber_name = rsData['chamber_name']
        recipe_name = rsData['recipe_name']
        sensor_cd = rsData['sensor_cd']
        print(rsData)
        print(equip_name)
        print(chamber_name)
        print(recipe_name)
        print(sensor_cd)
        print("=======")

        #학습 파일 경로 파악
        data = mmDataset.objects.filter(equip_name=equip_name, chamber_name=chamber_name, recipe_name=recipe_name, purpose='TRN').values_list('data_static_path', flat=True)
        path = rootpath + data[len(data) - 1]
        print(data)
        print(path)
        print("=======")

        #mh_monitoring 테이블에 관련 데이터를 저장하기 위하여 mm_model 테이블에서 정보를 조회한 뒤 테이블에 입력한다
        dataset_id = mmDataset.objects.filter(equip_name=equip_name, chamber_name=chamber_name, recipe_name=recipe_name, purpose='TRN').values_list('id', flat=True)
        dataset_id = dataset_id[len(dataset_id) - 1]
        model_id = mmModel.objects.filter(dataset_id=dataset_id).values_list('id', flat=True)

        print(dataset_id)
        print(model_id)
        print("=======")

        if len(model_id) > 0:
            model_id = model_id[len(model_id) - 1]
        else:
            model_id = 0

        print(model_id)
        #경로는 우선 monitoring_anmalies만 지정..
        try:
            with transaction.atomic():
                mhMonitoring.objects.create(
                    model_id=model_id,
                    warnlist_path=anomalies_path,
                    user_id=request.user.id
                )
        except Exception as e:
            traceback.print_exc()
            context['success'] = False
            context['message'] = 'DB 저장 작업에서 에러가 발생하였습니다!'
            return JsonResponse(context, content_type='application/json')

        #test용으로 센서 번호만 이렇게..
        #sensor_cd = 2

        #모니터링 작업을 위한 watchdog thread 생성
        #모니터링 경로가 존재하지 않는 경우에는 watchdog thread 실행후 센서 변경시 런타임 에러가 발생하므로
        #모니터링 파일 경로가 존재하는 경우에만 기능 동작하도록 처리
        if os.path.isdir(monitoring_path):
            # monitoring = Target()
            # monitoring.get_path(monitoring_path, sensor_cd, path, anomalies_path)
            # monitoring.daemon = True
            # monitoring.run()
            pass
        else:
            context['success'] = False
            context['message'] = '경로가 존재하지 않아 실행할 수 없습니다!'
            return JsonResponse(context, content_type='application/json')

        return JsonResponse(context, content_type='application/json')


class monitoring_upload(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        file = request.FILES.get('file', '')
        directory_name = request.POST['dir']
        sep = os.sep

        path = f'static{sep}data{sep}{directory_name}'

        if file == '':
            context['success'] = False
            context['message'] = '파일을 선택해주세요.'
            return JsonResponse(context, content_type='application/json')

        filename = file.name
        name_ext = os.path.splitext(filename)[1]
        
        #csv 파일만 저장되도록 지정
        if name_ext != '.csv':
            context['success'] = False
            context['message'] = 'csv 파일을 넣어주세요.'
            return JsonResponse(context, content_type='application/json')

        try:
            fs = FileSystemStorage(location=path)
            fs.save(f"{filename}", file)
            print(fs)
        except:
            context['success'] = False
            context['message'] = '업로드에 실패하였습니다.'
            return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['message'] = '업로드에 성공하였습니다.'
        return JsonResponse(context, content_type='application/json')


class execute_monitoring(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        rootpath = os.getcwd()
        sep = os.sep

        dir = rootpath + f"{sep}static{sep}data{sep}monitoring_anomalies" + sep
        file_list = os.listdir(dir)
        csv_list = []

        #파일을 생성시간순으로 정렬한 후 최신파일이 먼저 표현되도록 역순 정렬 처리..
        file_list.sort(key=lambda s: os.stat(os.path.join(dir, s)).st_ctime)
        file_list.reverse()

        '''for i in range(0, len(file_list)) :
            for j in range(0, len(file_list)) :
                if datetime.datetime.fromtimestamp(os.stat(dir + file_list[i]).st_mtime) < datetime.datetime.fromtimestamp(os.stat(dir + file_list[j]).st_mtime) :
                    (file_list[i], file_list[j]) = (file_list[j], file_list[i])'''

        #파일 리스트 전체의 csv파일 데이터를 읽어들여와 List 형식으로 변환(전체파일)
        for k in file_list :
            data = pandas.read_csv(dir + k, header = None)
            data = data.values.tolist()
            csv_list.append([k, data])

        context = {
            "anomalies_list": file_list,
            "csv_list" : csv_list
        }

        return JsonResponse(context, content_type='application/json')


class stop_thread(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        #global 변수를 이용하여 페이지를 종료하거나 이동하는 경우 기존에 동작중이던 모니터링 thread를 중단시킨다.
        global monitoring
        context = {}

        if monitoring != None :
            monitoring.run_stop()

        return JsonResponse(context, content_type='application/json')
