from django.views.generic import View
from django.shortcuts import render
from config.models import mmDataset, mmModel, mmRecipe
import json
import os
from django.http import HttpRequest, JsonResponse
from datetime import datetime
import pandas
from collections import Counter
from django.db import transaction
# from aiengine.learning_code import learn_anomaly
# from aiengine.test_code import test_anomaly
from django.contrib.auth.decorators import login_required

@login_required(None, None, "/login")
def training_main(request):
    context = {}

    trainDataList = mmDataset.objects.filter(purpose="TRN").order_by('-id')[:50]
    testDataList = mmDataset.objects.filter(purpose="TST").order_by('-id')[:50]
    context['trainDataList'] = trainDataList
    context['testDataList'] = testDataList

    query = '''
    SELECT id, AVG(TIMESTAMPDIFF(SECOND, a.train_start, a.train_end_test_start) / a.num_train) AS train, AVG(TIMESTAMPDIFF(SECOND, a.train_end_test_start, a.test_end) / a.num_test) AS test
    FROM mm_model a
    '''

    ProgressTime = mmModel.objects.raw(query)
    Time = 0
    for i in ProgressTime:
        train = i.train
        test = i.test
        print(Time)
        break

    context['TrainTime'] = train
    context['TestTime'] = test
    return render(request, 'old_training.html', context)


def init_graph(request):
    context = {}

    rootpath = os.getcwd()
    sep = os.sep
    if sep != '/':
        sep = r"\\"
    # save_filepath = os.path.join(rootpath, 'static', 'data', 'training_savefile.json')
    save_filepath = f'{rootpath}{sep}static{sep}data{sep}training_savefile.json'
    print("savefile::", save_filepath)
    if os.path.isfile(save_filepath):
        with open(save_filepath, 'r') as save_file:
            save_data = json.load(save_file)
            context = save_data
        print("context::", context)
    else:
        context['state'] = "InitFalse"
    return JsonResponse(context, content_type='application/json')

@login_required(None, None, "/login")
def start_training(request):
    context = {}
    rsData = json.loads(request.body.decode("utf-8"))
    print("!!!!!!!!!!!!!Start Training!!!!!!!!!!!!!")

    rootpath = os.getcwd()
    numTrain = rsData['numTrain']
    numTest = rsData['numTest']
    trainDataId = rsData['trainDataId']
    trainStaticPath = mmDataset.objects.filter(id=trainDataId)[0].data_static_path
    trainStaticPath = rootpath + trainStaticPath

    testDataId = rsData['testDataId']
    testStaticPath = mmDataset.objects.filter(id=testDataId)[0].data_static_path
    testStaticPath = rootpath + testStaticPath

    sensorNo = int(rsData['sensorNo'])
    thresholdStd = int(rsData['thresholdStd'])
    print("path::", trainStaticPath, testStaticPath)
    print(trainDataId, testDataId, sensorNo, thresholdStd)
    if (trainDataId != 'Null') & (testDataId != 'Null'):

        start_train = datetime.now()
        print(f'Start train.....{start_train}')
        # threshold_train, num_anomaly_train = learn_anomaly(sensorNo, thresholdStd, trainStaticPath)
        start_test = datetime.now()
        print(f'End train & start test.....{start_test}')
        # threshold_test, num_anomaly_test = test_anomaly(sensorNo, testStaticPath, trainStaticPath)
        end_test = datetime.now()
        print(f'End test.....{end_test}')

        recipeId = mmRecipe.objects.get(equip_name=rsData['equipName'], chamber_name=rsData['chamberName'], recipe_name=rsData['recipeName'],
                             revision_no=rsData['revisionNo'], sensor_cd=rsData['sensorNo']).id

        # print(rsData['equipName'])
        # print(rsData['chamberName'])
        # print(rsData['recipeName'])
        # print(rsData['revisionNo'])
        # print("ID::::::::", recipeId)
        # equip_name, chamber_name, recipe_name, revision_no, sensor_cd -> recipe id

        print("-------ㅡmodelCreate----------")
        try:
            with transaction.atomic():
                mmModel.objects.create(
                    #모델db 생성데이터
                    problem_id=1,
                    recipe_id=recipeId,
                    dataset_id=rsData['trainDataId'],
                    sensor_cd=sensorNo,
                    # threshold_train=threshold_train,
                    # threshold_test=threshold_test,
                    # num_anomaly_train=num_anomaly_train,
                    # num_anomaly_test=num_anomaly_test,
                    train_start=start_train,
                    train_end_test_start=start_test,
                    test_end=end_test,
                    num_train=numTrain,
                    num_test=numTest,
                )

            print("mmModel create 성공")
        except Exception as e:
            context['success'] = False
            context['message'] = 'DB 저장 실패'
            return JsonResponse(context, content_type='application/json')
        print("!!!!!!!!!!!!!End Training!!!!!!!!!!!!!")
    else:
        print("testdata, traindata모두 입력하세요.")
    return JsonResponse(context, content_type='application/json')


def graphing_training(request):
    context = {}
    print("graphing")###############
    rsData = json.loads(request.body.decode("utf-8"))

    rootpath = os.getcwd()
    sep = os.sep
    trainStaticPath = rsData['trainStaticPath']
    print("trainStaticPath1::", trainStaticPath)
    trainStaticPath = f"{rootpath}{sep}{trainStaticPath}"
    print("trainStaticPath2::", trainStaticPath)
    trainingStatusFile = trainStaticPath + f"{sep}after_learning{sep}plots{sep}Training_status_loss.csv"
    trainingAnomalyFile = trainStaticPath + f"{sep}after_learning{sep}plots{sep}train_anomaly_score.csv"
    thresholdFile = trainStaticPath + f"{sep}after_learning{sep}test_input{sep}threshold.txt"

    testStaticPath = rsData['testStaticPath']
    testStaticPath = f"{rootpath}{sep}{testStaticPath}"
    testAnomalyFile = testStaticPath + f"{sep}after_test{sep}plots{sep}test_anomaly_score.csv"
    testAnomalyList = testStaticPath + f'{sep}after_test{sep}anomalies{sep}'
    print("sep::", sep)
    print("trainStaticPath::", trainStaticPath)
    print("trainingStatusFile:::", trainingStatusFile)

    if os.path.isfile(trainingStatusFile) & os.path.isfile(testAnomalyFile):
        #3번그래프 데이터처리
        file_list = os.listdir(testAnomalyList)
        csv_list = []
        #   파일을 수정시간순으로 정렬
        file_list.sort(key=lambda s: os.stat(os.path.join(testAnomalyList, s)).st_ctime)
        file_list.reverse()
        #   파일 리스트 전체의 csv파일 데이터를 읽어들여와 List 형식으로 변환(전체파일)
        for k in file_list:
            data = pandas.read_csv(testAnomalyList + k, header = None)
            data = data.values.tolist()
            csv_list.append([k, data])

        #threshold
        thresholdpd = pandas.read_csv(thresholdFile, header=None)
        #      threshold 표시값 조정
        forAdjustThshld = 1000
        threshold = round(pandas.DataFrame(thresholdpd).loc[0, 0] * forAdjustThshld, 2)
        context = {'anomalies_list': file_list, 'csv_list': csv_list, 'current_threshold': threshold,
                   'status_loss': convert_data(trainingStatusFile, 0)[0],
                   'status_val_loss': convert_data(trainingStatusFile, 0)[1],
                   'train_anomaly_score': convert_data(trainingAnomalyFile, 1),
                   'test_anomaly_score': convert_data(testAnomalyFile, 1),
                   'state': "InitTrue"}
        print("anomaly_score:::: ", context['train_anomaly_score'])
        save_filepath = os.path.join(rootpath, 'static', 'data', 'training_savefile.json')
        # data file save
        with open(save_filepath, 'w') as save_file:
            json.dump(context, save_file)
        context['state'] = "True"
        return JsonResponse(context, content_type='application/json')
    else:
        context['state'] = "False"
        return JsonResponse(context, content_type='application/json')


def adjust_threshold(request):
    context = {}
    rsData = json.loads(request.body.decode("utf-8"))

    rootpath = os.getcwd()
    sep=os.sep
    trainStaticPath = rsData['trainStaticPath']
    thresholdFile = rootpath + trainStaticPath + f"{sep}after_learning{sep}test_input{sep}threshold.txt"

    file = open(thresholdFile, 'w')
    adjustThreshold = float(rsData['adjustThreshold']) / 1000
    file.write(str(adjustThreshold))
    file.close()

    return JsonResponse(context, content_type='application/json')


def convert_data(file, mthd):
    data = pandas.read_csv(file, header=None, encoding='cp949')
    # anomaly_score의 경우 mthd = 1
    if mthd == 0:
        data = data.values.tolist()
    elif mthd == 1:
        data = data.iloc[:, 0]
        data = round(data, 5)
        data = data.tolist()
        data = Counter(data)
        data = sorted(data.items())
        data = dict(data)
    return data
