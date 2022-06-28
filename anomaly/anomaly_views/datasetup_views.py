from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from django.core.files.storage import FileSystemStorage
from config.models import *
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from ..views import *
import json
import os
from datetime import datetime
import zipfile
import shutil
from anomaly_detection import train_data_gen


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


def get_csv_size(path):
    return path.stat().st_size


class DataSetupView(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        context['treedata'] = get_treestructure()
        context['username'] = request.user.username

        return render(request, 'datasetup.html', context)


class Datalist(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        path = data['path']

        dirpath = Path(BASE_DIR) / 'static' / 'data' / 'sensor'
        for i in range(len(path)):
            dirpath = dirpath / path.pop()

        trnpath = dirpath / 'raw_data_csv'

        trndraw = rawlist(trnpath)

        if len(trndraw) == 0:
            flag = 'no'
            context['flag'] = flag
            return JsonResponse(context, content_type='application/json')
        else:
            flag = 'yes'
        a = MakePandas(trndraw)
        sendlist = a.valuelist()
        indexlist = a.indexlist()

        context['flag'] = flag
        context['trnlist'] = sendlist
        context['index'] = indexlist
        mindate = list(a.datelist())[0]
        maxdate = list(a.datelist())[1]
        print(mindate, maxdate)
        context['mindate'] = datetime.strftime(mindate, '%Y-%m-%d')
        context['maxdate'] = datetime.strftime(maxdate, '%Y-%m-%d')
        return JsonResponse(context, content_type='application/json')


class Search(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        path = data['path']
        starttime = data['start']
        endtime = data['end']
        lot = data['lot']
        wafer = data['wafer']

        startdate = datetime.strptime(starttime, '%Y-%m-%d')
        enddate = datetime.strptime(endtime, '%Y-%m-%d')

        dirpath = Path(BASE_DIR) / 'static' / 'data' / 'sensor'
        for i in range(len(path)):
            dirpath = dirpath / path.pop()
        trnpath = dirpath / 'raw_data_csv'
        trndraw = rawlist(trnpath)

        a = MakePandas(trndraw)
        a.filterpd(startdate, enddate, lot, wafer)
        sendlist = a.valuelist()
        indexlist = a.indexlist()
        if len(sendlist) == 0:
            flag = 'no'
        else:
            flag = 'yes'
        context['flag'] = flag
        context['trnlist'] = sendlist
        context['index'] = indexlist
        return JsonResponse(context, content_type='application/json')


class SetData(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        print('datasetup start======')
        data = request.body.decode('utf-8')
        data = json.loads(data)
        path = data['path']
        idlist = data['idlist']

        dirpath = Path(BASE_DIR) / 'static' / 'data' / 'sensor'
        for i in range(len(path)):
            dirpath = dirpath / path.pop()
        trnpath = dirpath / 'raw_data_csv'
        trndraw = rawlist(trnpath)

        a = MakePandas(trndraw)
        trn = a.settraindata(idlist)
        tst = a.settestdata(idlist)

        # 생성 전 디렉토리 초기화
        train_input = dirpath / 'train_data'
        test_input = dirpath / 'test_data'
        try:
            for file in os.listdir(train_input):
                file_path = os.path.join(train_input, file)
                os.remove(file_path)
            for file in os.listdir(test_input):
                file_path = os.path.join(test_input, file)
                os.remove(file_path)
        except OSError:
            print('csv remove error')
            context['flag'] = 0
            return JsonResponse(context, content_type='application/json')

        try:
            for idx, row in tst.iterrows():
                filedate = datetime.strftime(row.date, '%Y_%m_%d')
                filelot = row.lot
                filewafer = row.wafer
                filename = f'{filedate}_{filelot}_{filewafer}.csv'
                inputfile = trnpath / filename
                outputfile = dirpath / 'test_data' / filename

                shutil.copyfile(inputfile, outputfile)

            for idx, row in trn.iterrows():
                filedate = datetime.strftime(row.date, '%Y_%m_%d')
                filelot = row.lot
                filewafer = row.wafer
                filename = f'{filedate}_{filelot}_{filewafer}.csv'
                inputfile = trnpath / filename
                outputfile = dirpath / 'train_data' / filename

                shutil.copyfile(inputfile, outputfile)
        except FileNotFoundError:
            print('csv data error')
            context['flag'] = 0
            return JsonResponse(context, content_type='application/json')

        train_input = dirpath / 'train_data'
        str_train = str(train_input)
        test_input = dirpath / 'test_data'
        str_test = str(test_input)
        train_npy = str(train_input / 'output.npy')
        test_npy = str(test_input / 'output.npy')

        try:
            train_data_gen.gen_tensor(str_train)
            train_data_gen.gen_tensor(str_test)
            train_data_gen.train_data_gen(train_npy, str_train)
            train_data_gen.test_data_gen(test_npy, str_test, str_train)
        except FileNotFoundError:
            print('gen_tensor error')
            context['flag'] = 0
            return JsonResponse(context, content_type='application/json')

        # npy, pkl 생성 후 csv 삭제
        try:
            for file in os.listdir(train_input):
                name, ext = os.path.splitext(file)
                if ext == '.csv' and name != 'train_normal_mm':
                    file_path = os.path.join(train_input, file)
                    os.remove(file_path)
            for file in os.listdir(test_input):
                name, ext = os.path.splitext(file)
                if ext == '.csv' and name != 'test_bad_mm' and name != 'test_normal_mm':
                    file_path = os.path.join(test_input, file)
                    os.remove(file_path)
        except OSError:
            print('csv remove error')
            context['flag'] = 0
            return JsonResponse(context, content_type='application/json')

        context['flag'] = 1
        return JsonResponse(context, content_type='application/json')


class MakePandas:
    def __init__(self, data):
        data_all = []
        del data[-1]  # sensor_info.txt 제거
        for title in data:
            title_date = title[:10]
            title_lot = title[11:-7]
            title_wafer = title[-6:-4]
            data_one = [title_date, title_lot, title_wafer]
            data_all.append(data_one)
        data_pd = pd.DataFrame(data_all, columns=['date', 'lot', 'wafer'])
        data_pd = data_pd.sort_values(by=['date', 'lot', 'wafer'], ascending=[False, True, True])
        data_pd['date'] = data_pd['date'].apply(lambda _: datetime.strptime(_, '%Y_%m_%d'))
        self.data_pd = data_pd
        self.filter_pd = None

    def getpd(self):
        return self.data_pd

    def filterpd(self, starttime, endtime, lot, wafer):
        startdate = self.data_pd['date'] >= starttime   # 1st 조건에 해당하는 데이터 저장
        enddate = self.data_pd['date'] <= endtime       # 2nd 조건에 해당하는 데이터 저장
        lot_search = self.data_pd['lot'].str.contains(lot)
        wafer_search = self.data_pd['wafer'].str.contains(wafer)
        datepd = self.data_pd[startdate & enddate & lot_search & wafer_search]      # 두 조건으로 필터링
        self.filter_pd = datepd

    def valuelist(self):
        if self.filter_pd is None:
            send_pd = self.data_pd
        else:
            send_pd = self.filter_pd
        val_list = send_pd.values.tolist()
        return val_list

    def indexlist(self):
        if self.filter_pd is None:
            send_pd = self.data_pd
        else:
            send_pd = self.filter_pd
        index_list = send_pd.index.tolist()
        return index_list

    def datelist(self):
        maxdate = self.data_pd['date'].max()
        mindate = self.data_pd['date'].min()
        return mindate, maxdate

    def settraindata(self, idlist):
        train_pd = self.data_pd.drop(index=idlist)
        return train_pd

    def settestdata(self, idlist):
        test_pd = self.data_pd.loc[idlist]
        return test_pd


class RawConvert(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}
        data = request.body.decode('utf-8')
        data = json.loads(data)
        path = data['path']
        # root path
        rootpath = Path(BASE_DIR) / 'static' / 'data' / 'sensor'
        for i in range(len(path)):
            rootpath = rootpath / path.pop()
        # input path
        inputpath = rootpath / 'raw_data'
        print(inputpath)
        # output path
        outputpath = rootpath / 'raw_data_csv'

        flag = train_data_gen.excute_d_g(inputpath, outputpath)
        if flag is not True:
            context['flag'] = False
        else:
            context['flag'] = True
        return JsonResponse(context, content_type='application/json')
