from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from config.models import mmDataset, mmModel, mmRecipe
from django.http import HttpRequest, JsonResponse
import json
import os
import time
import pandas
from datetime import datetime
import numpy as np


class analysis_main(LoginRequiredMixin, View):
    login_url = '/login'
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        sep = os.sep
        query1 = request.GET.get('date_start', 'Null')
        query2 = request.GET.get('date_end','Null')
        #querystring 없이 순수 url 접속시
        if (query1 == 'Null') & (query2 == 'Null'):
            context['treedata'] = get_treestructure()
            return render(request, "analysis.html", context)

        today = datetime.today().strftime("%Y-%m-%d")
        date_start = request.GET.get('date_start', today)
        date_end = request.GET.get('date_end', today)
        formatted_enddate = time.strptime(date_end,"%Y-%m-%d")
        formatted_startdate = time.strptime(date_start,"%Y-%m-%d")

        tree_selected = request.GET.get('tree_checked_ids')
        # 파일 경로 및 파일명에는 ',' '#'"가 들어가면 안됨
        tree_selected_list = tree_selected.split(",")

        for selected_sensor in tree_selected_list:
            sensor_list = []
            temp = selected_sensor.split('#')
            datapath = temp[0]
            sensor_list.append(int(temp[1].replace("employee", '')))

            datapath = datapath + sep
            # print("datapath::::", datapath)
            # print("sensornum:::", sensor_list)

            file_list = os.listdir(datapath)
            file_list_csv = [file for file in file_list if file.endswith(".csv")]
            print("all_list::: ", file_list_csv)
            filtered_filelist = []
            # 기간내 파일 필터링
            for i in file_list_csv:
                date = i[:10]
                formatted_file_date = time.strptime(date, "%Y_%m_%d")
                if (formatted_startdate <= formatted_file_date and formatted_file_date <= formatted_enddate):
                    filtered_filelist.append(i)

            #test
            # print("files:::::::", filtered_filelist)

            d1_datasum = []
            csv_data = []
            for k in filtered_filelist:
                data = pandas.read_csv(datapath + k, header=None)
                for sensor_num in sensor_list:
                    sensor_data = data.iloc[:, sensor_num]
                    sensor_data = sensor_data.values.transpose().tolist()
                    d1_data = np.reshape(sensor_data, -1)
                    d1_datasum.extend(d1_data)
                    csv_data.append([k, sensor_data])

            #anomaly 데이터처리(시간필터링 x)
            rootpath = os.getcwd()

            anomaly_datapath = f"{sep}static{sep}data{sep}monitoring_anomalies" + sep
            anomaly_path = rootpath + anomaly_datapath
            anomaly_filelist = os.listdir(anomaly_path)
            anomaly_csv_data = []
            anomaly_csv_fulldata = []
            #   파일을 수정시간순으로 정렬
            anomaly_filelist.sort(key=lambda s: os.stat(os.path.join(anomaly_path, s)).st_ctime)
            anomaly_filelist.reverse()
            #   파일 리스트 전체의 csv파일 데이터를 읽어들여와 List 형식으로 변환(전체파일)
            for k in anomaly_filelist:
                anomaly_data = pandas.read_csv(anomaly_path + k, header=None, )
                anomaly_data = anomaly_data.values.tolist()
                anomaly_csv_fulldata.append([k, anomaly_data])
                anomaly_csv_data.append(anomaly_data[0])
                anomaly_csv_data.append(anomaly_data[1])
                d1_datasum.extend(np.reshape(anomaly_data[0], -1))
                d1_datasum.extend(np.reshape(anomaly_data[1], -1))

        # calculate mean, std
        mean_val = np.mean(d1_datasum)
        std_val = np.std(d1_datasum)
        print("mean::", mean_val, "std::", std_val)
        ori_data = []
        for j in range(0, len(csv_data)):
            ori_data.append(csv_data[j][1])
        # mean,std 이용한 normalization
        normalized_data = []
        normalized_anomaly_csvdata = []
        for l in range(0, len(csv_data)):
            normalized_data.append(list(map(lambda element: normalize(element, mean_val, std_val), ori_data[l])))
        for m in range(0, len(anomaly_csv_data)):
            normalized_anomaly_csvdata.append(list(map(lambda element: normalize(element, mean_val, std_val), anomaly_csv_data[m])))

        context['raw_data'] = csv_data
        context['normalized_data'] = normalized_data
        context['anomaly_filelist'] = anomaly_filelist
        context['anomaly_csvdata'] = anomaly_csv_data
        context['normalized_anomaly_csvdata'] = normalized_anomaly_csvdata
        context['anomaly_csv_fulldata'] = anomaly_csv_fulldata

        # print("raw_data:::::::::", context['raw_data'])
        # print("normilized_data:::::::::", context['normalized_data'])
        # print("anomaly_filelist:::::::::::::", context['anomaly_filelist'])
        # print("anomaly_csvdata::::::::::::", context['anomaly_csvdata'])
        # print("normalized_anomaly_csvdata::::::", context['normalized_anomaly_csvdata'])
        print("anomaly_csv_fulldata:::: ", context['anomaly_csv_fulldata'])
        return JsonResponse(context, content_type='application/json')


def normalize(element, mean, std):
    return (element-mean)/std


def get_treestructure():
    equip_list = mmDataset.objects.filter().order_by('equip_name').values_list('equip_name').distinct()
    treedata = ""
    # checkbox_state = '{ "checkbox_disabled" : true }'
    state_open = '{ "opened": true }'
    for i in equip_list:
        line = f'"id":"{i[0]}", "parent":"#", "text":"{i[0]}", "state" : {state_open}'
        treedata += '{' + line + '}, '
        chamber_list = mmDataset.objects.filter(equip_name=i[0]).values_list('chamber_name').distinct()
        for j in chamber_list:
            line = f'"id":"{i[0]}{j[0]}", "parent":"{i[0]}", "text":"{j[0]}", "state" : {state_open}'
            treedata += '{' + line + '}, '
            recipe_list = mmDataset.objects.filter(equip_name=i[0], chamber_name=j[0]).values_list('recipe_name').distinct()
            for k in recipe_list:
                line = f'"id":"{i[0]}{j[0]}{k[0]}", "parent":"{i[0]}{j[0]}", "text":"{k[0]}"'
                treedata += '{' + line + '}, '
                rev_list = mmDataset.objects.filter(equip_name=i[0], chamber_name=j[0], recipe_name=k[0]).values_list('revision_no').distinct()
                rootpath=os.getcwd()
                rootpath = rootpath.replace('\\', '\\\\')
                for l in rev_list:
                    data_path = rootpath + mmDataset.objects.filter(equip_name=i[0], chamber_name=j[0], recipe_name=k[0], revision_no=l[0]).last().data_static_path
                    line = f'"id":"{i[0]}{j[0]}{k[0]}{l[0]}", "parent":"{i[0]}{j[0]}{k[0]}", "text":"{l[0]}", "val":"{data_path}"'#, "state" : {checkbox_state}'
                    treedata += '{' + line + '}, '
                    sensorinfo_file = os.path.join(data_path, "sensor_info.txt")
                    if os.path.isfile(sensorinfo_file):
                        file = open(sensorinfo_file, "r")
                        sensors_txt = file.read()
                        file.close()
                        sensor_list = sensors_txt.strip().split(", ")[1:]
                        for m in sensor_list:
                            sensor_id = data_path + '#' + m
                            line = f'"id":"{sensor_id}", "parent":"{i[0]}{j[0]}{k[0]}{l[0]}", "text":"{m}"'
                            treedata += '{' + line + '}, '
    treedata = treedata[:-2]
    treedata = '[' + treedata + ']'
    return treedata
