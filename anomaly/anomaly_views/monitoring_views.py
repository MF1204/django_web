from django.views.generic import View
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from ..views import get_treestructure
import os
import json
import random
import sys
import threading
from pathlib import Path
import numpy as np
import torch
from django.apps import AppConfig
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import time
from anomaly_detection import main_test, monitoring_data_gen_yj
from config.settings import BASE_DIR


monitoring_observer = Observer()


class Monitoring(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {
            'treedata': get_treestructure()
        }
        print(BASE_DIR)
        return render(request, 'monitoring.html', context)


def monitoring_stop(request):
    global monitoring_observer
    monitoring_observer.stop()

    rsData = json.loads(request.body.decode('utf-8'))
    flag = rsData['flag']

    context = {
        'flag': True
    }
    return JsonResponse(context, content_type='application/json')


def monitoring_start(request):
    global monitoring_observer
    rsData = json.loads(request.body.decode("utf-8"))
    flag = rsData['flag']
    print("file system handler start")

    static_path = Path(BASE_DIR) / 'static' / 'data' / 'sensor'

    event_handler = DrsHandler()
    monitoring_observer.schedule(event_handler, path=str(static_path / 'P001'), recursive=True)
    monitoring_observer.schedule(event_handler, path=str(static_path / 'P002'), recursive=True)
    monitoring_observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitoring_observer.stop()
        print('Monitoring Error')

    context = {
        'flag': True
    }
    return JsonResponse(context, content_type='application/json')


class DrsHandler(FileSystemEventHandler):
    def on_created(self, event):
        file_extension = os.path.splitext(event.src_path)[1]
        dir_name = event.src_path.split(os.sep)[-2]
        if file_extension != '.drs' or dir_name != 'monitoring':
            return
        drs = str(event.src_path)   # drs file
        monitoring_path = get_monitoring_path(drs)
        model = get_model_path(drs)  # model file
        feature_list = get_feature_list(drs)
        threshhold = get_threshhold_path(drs)
        minmax = get_minmax_path(drs)
        score = get_score_path(drs)

        train_config = set_train_config()
        env_config = set_env_config(drs, monitoring_path, model, feature_list, threshhold, minmax, score)

        inference_run(train_config, env_config)


def get_recipe_path(drs_file_path):
    sep = os.sep

    get_full_path = os.path.dirname(drs_file_path)
    data_path = Path('static') / 'data' / 'sensor'
    find_data_path = drs_file_path.find(str(data_path)) + len(str(data_path))
    recipe_information = get_full_path[find_data_path + len(sep):].split(sep)[:-1]
    recipe_path = os.path.join(*recipe_information)

    return recipe_path


def get_model_path(drs_file_path):

    recipe_path = get_recipe_path(drs_file_path)
    model_path_front = Path('static') / 'ai_model' / 'anomaly'
    model_path_back = Path('model') / 'version_00' / 'pretrained'

    pretrained_model_directory = os.path.join(BASE_DIR, model_path_front, recipe_path, model_path_back)
    model_pt_list = os.listdir(pretrained_model_directory)
    model_pt_file = model_pt_list[0]
    model_pt_path = Path(pretrained_model_directory) / str(model_pt_file)

    return model_pt_path


def get_threshhold_path(drs_file_path):

    recipe_path = get_recipe_path(drs_file_path)
    threshhold_front = Path('static') / 'ai_model' / 'anomaly'
    threshhold_back = Path('results') / 'threshhold.npy'

    threshhold_path = os.path.join(BASE_DIR, threshhold_front, recipe_path, threshhold_back)
    return threshhold_path


def get_minmax_path(drs_file_path):

    recipe_path = get_recipe_path(drs_file_path)
    minmax_front = Path('static') / 'data' / 'sensor'
    minmax_back = Path('train_data') / 'minmax_scalar.pkl'

    minmax_path = os.path.join(BASE_DIR, minmax_front, recipe_path, minmax_back)
    return minmax_path


def get_score_path(drs_file_path):

    recipe_path = get_recipe_path(drs_file_path)
    score_front = Path('static') / 'data' / 'sensor'
    score_back = 'monitoring_result'

    score_path = os.path.join(BASE_DIR, score_front, recipe_path, score_back)
    return score_path


def get_monitoring_path(drs_file_path):

    recipe_path = get_recipe_path(drs_file_path)
    monitoring_front = Path('static') / 'data' / 'sensor'
    monitoring_back = 'monitoring'

    score_path = os.path.join(BASE_DIR, monitoring_front, recipe_path, monitoring_back)
    return score_path


def get_feature_list(drs_file_path):
    recipe_path = get_recipe_path(drs_file_path)
    feature_front = Path('static') / 'data' / 'sensor'
    feature_back = Path('train_data') / 'list.txt'
    feature_list_path = os.path.join(BASE_DIR, feature_front, recipe_path, feature_back)
    return feature_list_path


def set_train_config():
    train_config = {
        'batch': 128,
        'epoch': 3,
        'slide_win': 5,
        'dim': 50,
        'slide_stride': 5,
        'comment': '',
        'seed': 0,
        'out_layer_num': 1,
        'out_layer_inter_dim': 256,
        'decay': float(0),
        'val_ratio': float(0.2),
        'topk': 0,
    }
    return train_config


def set_env_config(drs, monitoring_path, model, feature_list, threshhold, minmax, score):
    env_config = {
        'device': 'cuda',
        'report': 'val',
        'drs_input': drs,
        'monitoring_path': monitoring_path,
        'model_input': model,
        'feature_input': feature_list,
        'threshhold_input': threshhold,
        'minmax_input': minmax,
        'score_output': score,
    }
    return env_config


def inference_run(train_config, env_config):
    random_seed = 0
    torch.manual_seed(random_seed)
    torch.cuda.manual_seed(random_seed)
    torch.cuda.manual_seed_all(random_seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(random_seed)
    random.seed(random_seed)

    os.environ['PYTHONHASHSEED'] = str(random_seed)

    drs_input = env_config['drs_input']
    minmax_input = env_config['minmax_input']

    monitoring_data_gen_yj.data_gen(drs_input, minmax_input)
    file_ext = r'.csv'
    raw_list = [file for file in os.listdir(get_monitoring_path(drs_input)) if file.endswith(file_ext)]
    print(raw_list)
    anomaly_list = []
    for file in raw_list:
        main = main_test.Main(file, train_config, env_config, debug=False)
        anomaly_decision = main.run(file)
        lot_info = file.split(".")
        if anomaly_decision[0]:
            anomaly_list.append(lot_info[0])
        csv_file = Path(env_config['monitoring_path']) / str(file)
        # os.remove(csv_file)

    print('===========Error Report==========')
    if not anomaly_list:
        print('There is no anomaly')
    else:
        print(anomaly_list)
    print(f'Total Number of anomaly samples: {len(anomaly_list)}')
