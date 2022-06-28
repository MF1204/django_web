from django.shortcuts import render
from config.models import info_dataset, info_recipe, info_training, profile
import json
import os
from pathlib import Path
from django.http import HttpRequest, JsonResponse
from datetime import datetime
from django.db import transaction
from ..views import get_treestructure
from .datasetup_views import get_csv_size
from config.settings import BASE_DIR
from anomaly_detection.main import Main
from anomaly_detection.evaluate import get_threshhold
import pandas
import numpy as np
from collections import Counter


def training_main(request):
    context = {}

    query = '''
    SELECT TRN.id, AVG(TIMESTAMPDIFF(SECOND, TRN.train_start, TRN.train_end) * 1000 / (TRN.traindata_size + TRN.testdata_size) / 1024) AS time
    FROM info_training AS TRN
    '''
    progresstime = info_training.objects.raw(query)
    time = 0
    for i in progresstime:
        time = i.time
        print(time)
        break

    context['treedata'] = get_treestructure()
    context['progressTime'] = time

    return render(request, 'training.html', context)


def training_start(request):
    context = {}
    rsData = json.loads(request.body.decode("utf-8"))
    print("Training Start")

    recipe_id = info_recipe.objects.get(code=rsData['recipeName'], revision=0)
    dataset = Path(rsData['processName']) / rsData['equipName'] / rsData['chamberName'] / rsData['recipeName']
    try:
        version = info_training.objects.filter(recipe_id=recipe_id).count()
    except Exception as e:
        version = 0
        print(version)
        print(e)

    register = profile.objects.get(user_id=request.user.id)

    root_path = Path(BASE_DIR) / 'static' / 'data' / 'sensor' / dataset
    traindata_size = get_csv_size(root_path / 'train_data' / 'train_normal_mm.csv')
    testdata_size = get_csv_size(root_path / 'test_data' / 'test_bad_mm.csv')
    print(traindata_size)
    print(testdata_size)
    # 버전 관리 추가

    train_config = {
        'batch': 128,   # batch size, type:int
        'epoch': 3,   # train epoch, type:int
        'slide_win': 5,   # slide_win, type:int
        'dim': 50,   # dimension, type:int
        'slide_stride': 5,   # slide_stride, type:int
        'comment': '',   # experiment comment, type:str
        'seed': 0,   # random seed, type:int
        'out_layer_num': 1,   # outlayer_num, type:int
        'out_layer_inter_dim': 256,   # out_layer_inter_dim, type:int
        'decay': 0,   # decay, type:float
        'val_ratio': 0.2,   # val ratio, type:float
        'topk': 0,   # topk num, type:int
    }

    env_config = {
        'save_path': '',   # save path pattern, type:str
        'dataset': dataset,   # wadi / swat, type:str, 공정/장비/챔버/레시피 경로
        'report': 'val',   # best / val, type:str
        'device': 'cuda',   # cuda / cpu, type:str
        'load_model_path': '',   # trained model path, type:str
        'version': 0,   # version, type:int, 모델 버전
    }

    main = Main(train_config, env_config, 105, debug=False)

    start_train = datetime.now()
    main.run()
    end_train = datetime.now()

    # DB관리 추가
    
    print("---------- training DB ----------")
    try:
        with transaction.atomic():
            info_training.objects.create(
                recipe_id=recipe_id,
                traindata_size=traindata_size,
                testdata_size=testdata_size,
                static_path=dataset,
                train_start=start_train,
                train_end=end_train,
                version=version,
                register=register,
                usage_flag=1
            )
        print("info_training create 성공")

    except Exception as e:
        context['success'] = False
        print(e)
        return JsonResponse(context, content_type='application/json')

    print("End Training")
    context['success'] = True
    return JsonResponse(context, content_type='application/json')


def training_graph(request):
    context = {}
    rsData = json.loads(request.body.decode("utf-8"))
    process = rsData['processName']
    equipment = rsData['equipName']
    chamber = rsData['chamberName']
    recipe = rsData['recipeName']

    rootpath = Path(BASE_DIR) / 'static' / 'ai_model' / 'anomaly'
    resultpath = rootpath / process / equipment / chamber / recipe / 'results'

    val_predicted_path = str(resultpath / 'val_predicted.csv')
    val_ground_path = str(resultpath / 'val_ground.csv')
    threshhold_path = str(resultpath / 'threshhold.npy')
    test_predicted_path = str(resultpath / 'test_predicted.csv')
    test_ground_path = str(resultpath / 'test_ground.csv')

    threshhold_arr = round_data(np.load(threshhold_path)[0])
    val_score_arr = convert_list_dict(np.load(str(resultpath / 'val_scores.npy')))
    test_score_arr = convert_list_dict(np.load(str(resultpath / 'test_scores.npy')))

    context = {
        'state': True,
        'val_predicted': convert_data(val_predicted_path, 0),
        'val_ground': convert_data(val_ground_path, 0),
        'val_scores': val_score_arr,
        'threshhold': threshhold_arr,
        'test_scores': test_score_arr,
        'test_predicted': convert_data(test_predicted_path, 0),
        'test_ground': convert_data(test_ground_path, 0),
    }

    return JsonResponse(context, content_type='application/json')


def convert_data(file, mthd):
    data = pandas.read_csv(file, header=None, encoding='cp949')
    # score의 경우 mthd = 1
    datadict = {}
    if mthd == 0:
        for item in data.iteritems():
            datalist = item[1].tolist()
            datadict[item[0]] = datalist
        data = datadict
    elif mthd == 1:
        for item in data.iteritems():
            datalist = round(item[1], 5)
            datalist = datalist.tolist()
            datalist = Counter(datalist)
            datalist = sorted(datalist.items())
            datalist = dict(datalist)
            datadict[item[0]] = datalist
        data = datadict
    return data


def round_data(data):
    new_arr = []
    for i in data:
        new_arr.append(round(i, 4))
    return new_arr


def convert_list_dict(dictlist):
    result_list = []
    for i in dictlist:
        round_bins = round_data(i[1])
        onedict = {'hist': list(i[0]), 'bins': round_bins}
        result_list.append(onedict)
    return result_list


def get_data_size(request):
    rsData = json.loads(request.body.decode("utf-8"))
    process = rsData['processName']
    equipment = rsData['equipName']
    chamber = rsData['chamberName']
    recipe = rsData['recipeName']
    path = Path(BASE_DIR) / 'static' / 'data' / 'sensor' / process / equipment / chamber / recipe
    trainpath = path / 'train_data' / 'train_normal_mm.csv'
    testpath = path / 'test_data' / 'test_bad_mm.csv'

    context = {'datasize': get_csv_size(trainpath) + get_csv_size(testpath)}
    print(path)
    print(context)
    return JsonResponse(context, content_type='application/json')