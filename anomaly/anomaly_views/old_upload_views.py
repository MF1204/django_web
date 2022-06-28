from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from django.core.files.storage import FileSystemStorage
from config.models import mmDataset, mmProblem, mmRecipe, mmEquipspec
from django.db import transaction

from django.shortcuts import render, redirect, get_object_or_404

import os
import zipfile
import shutil


def createDirectory(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            print('Already exists')
    except OSError:
        print("Error: Failed to create the directory.")


def get_dir_size(path):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total


class DataUploadView(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}
        context['username'] = request.user.username
        equip_name = request.GET.get('equip_name', '')
        chamber_name = request.GET.get('chamber_name', '')
        recipe_name = request.GET.get('recipe_name', '')
        revision_no = request.GET.get('revision_no', '')
        type = request.GET.get('type', 'train_data')
        if type == 'train_data':
            purpose = 'TRN'
        elif type == 'test_data':
            purpose = 'TST'

        rsEquip = mmRecipe.objects.all().values_list('equip_name', flat=True).distinct()
        context['rsEquip'] = rsEquip
        if rsEquip and equip_name == '':
            equip_name = rsEquip[0]

        context['equip_name'] = equip_name

        rsChamber = mmRecipe.objects.filter(equip_name=equip_name).values_list('chamber_name', flat=True).distinct()
        context['rsChamber'] = rsChamber
        if rsChamber and chamber_name == '':
            chamber_name = rsChamber[0]
        context['chamber_name'] = chamber_name

        rsRecipe = mmRecipe.objects.filter(equip_name=equip_name).values_list('recipe_name', flat=True).distinct()
        context['rsRecipe'] = rsRecipe
        if rsRecipe and recipe_name == '':
            recipe_name = rsRecipe[0]
        context['recipe_name'] = recipe_name

        rsRevision = mmRecipe.objects.filter(equip_name=equip_name, recipe_name=recipe_name).values_list('revision_no',
                                                                                                         flat=True).distinct()
        context['rsRevision'] = rsRevision
        if rsRevision and revision_no == '':
            revision_no = rsRevision[0]
        context['revision_no'] = revision_no

        rsDataset = mmDataset.objects.filter(equip_name=equip_name, chamber_name=chamber_name, recipe_name=recipe_name,
                                             revision_no=revision_no, purpose=purpose, delete_flag='0').order_by('-id')

        data_cnt = rsDataset.count()
        context['data_cnt'] = data_cnt
        context['rsDataset'] = rsDataset
        context['purpose'] = purpose

        return render(request, 'old_dataupload.html', context)

    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        equip_name = request.POST['equip_name']
        chamber_name = request.POST['chamber_name']
        recipe_name = request.POST['recipe_name']
        revision_no = request.POST['revision_no']
        data_cnt = request.POST['data_cnt']

        file = request.FILES.get('file', '')
        type = request.POST['inlineRadioOptions']

        sep = os.sep
        print("sep::", sep, ":::")
        if sep != '/':
            sep = r'\\'

        if file == '':
            context['success'] = False
            context['message'] = '파일을 선택해주세요.'
            return JsonResponse(context, content_type='application/json')

        filename = file.name
        filename_name = os.path.splitext(filename)[0]
        name_ext = os.path.splitext(filename)[1]

        if name_ext != '.zip':
            context['success'] = False
            context['message'] = 'zip 파일을 넣어주세요.'
            return JsonResponse(context, content_type='application/json')

        # TST, TRN (db 저장코드)
        if type == 'train_data':
            purpose = 'TRN'
        elif type == 'test_data':
            purpose = 'TST'

        directory_name = f'{equip_name}_{chamber_name}_{recipe_name}_{revision_no}'
        # path = f'static/data/{directory_name}/{type}'
        # path = os.path.join('static','data' ,directory_name ,type)
        path = f'static{sep}data{sep}{directory_name}{sep}{type}'
        save_dir_name = f'data{int(data_cnt) + 1}'

        try:
            with transaction.atomic():

                createDirectory(path)
                fs = FileSystemStorage(location=path)
                fs.save(f"{filename}", file)
                # csv파일 개수
                csv_cnt = 0
                with zipfile.ZipFile(f'{path}{sep}{filename}', 'r') as zipObj:
                    listOfFileNames = zipObj.namelist()
                    inner_dir_name = listOfFileNames[0][:-1]
                    if inner_dir_name != filename_name:
                        os.remove(os.path.join(path, filename))
                        raise Exception('zip파일 명과 zip파일 내 폴더명을 일치 시켜주세요.')
                    for fileName in listOfFileNames:
                        if fileName.endswith("csv"):
                            csv_cnt += 1
                            zipObj.extract(fileName, f'{path}')
                        elif fileName.endswith("npy"):
                            zipObj.extract(fileName, f'{path}')
                        elif fileName.endswith("txt"):
                            zipObj.extract(fileName, f'{path}')
                        elif fileName.endswith("pickle"):
                            zipObj.extract(fileName, f'{path}')

                os.remove(f'{path}{sep}{filename}')
                if os.path.exists(f'{path}{sep}__MACOSX'):
                    shutil.rmtree(f'{path}{sep}__MACOSX')
                os.rename(f'{path}{sep}{filename_name}', f'{path}{sep}{save_dir_name}')

                # 용량(바이트)
                data_size = get_dir_size(f'{path}{sep}{save_dir_name}')
                mmDataset.objects.create(
                    equip_name=equip_name,
                    chamber_name=chamber_name,
                    recipe_name=recipe_name,
                    revision_no=revision_no,
                    data_static_path=sep + f'{path}{sep}{save_dir_name}',
                    purpose=purpose,
                    data_name=save_dir_name,
                    data_cnt=csv_cnt,
                    data_size=data_size
                )

        except Exception as e:
            if os.path.exists(f'{path}{sep}{save_dir_name}'):
                shutil.rmtree(f'{path}{sep}{save_dir_name}')
            context['success'] = False
            context['message'] = '업로드 실패! \n' + str(e)
            return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['message'] = '업로드 성공!'
        return JsonResponse(context, content_type='application/json')
