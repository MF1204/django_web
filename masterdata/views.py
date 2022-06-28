from datetime import datetime
import os
from pathlib import Path
from django.apps import AppConfig
from config.settings import BASE_DIR


# ======== 기초코드부여 ========
def serial(code):
    codestr = str(code)[0]
    codenum = int(str(code)[1:]) + 1
    result = codestr + str(codenum).zfill(3)
    return result


def username(code):

    year = str(datetime.today().year)[2:]
    print(year)
    if code == '0':
        num = 1
    else:
        num = int(str(code)[2:]) + 1
        print(num)
    result = year + str(num).zfill(4)
    print('사번' + result)
    return result


# ======== filesystem view ========

# 서버구동시 최초 실행
class StaticDataDirectory(AppConfig):
    name = 'masterdata'
    run_already = False

    def ready(self):
        if StaticDataDirectory.run_already:
            return
        StaticDataDirectory.run_already = True

        datapath = Path(BASE_DIR) / 'static' / 'data'
        modelpath = Path(BASE_DIR) / 'static' / 'ai_model'
        if os.path.exists(datapath) and os.path.exists(modelpath):
            print('BASE directory is already exist')
            return
        else:
            # data dir
            data = datalist()
            for one in data:
                createdirectory(datapath / one)
            # model dir
            solution = solutionlist()
            for appname in solution:
                createdirectory(modelpath / appname)


def makedirectory(*args):
    model_makedirectory(*args)
    data_makedirectory(*args)


# model - solutionlist
def model_makedirectory(*args):
    solution = solutionlist()
    for appname in solution:
        pathstr = Path(BASE_DIR) / 'static' / 'ai_model' / appname
        result = makepath(pathstr, *args)
        createdirectory(result)


# data - datalist
def data_makedirectory(*args):
    data = datalist()
    for dataname in data:
        pathstr = Path(BASE_DIR) / 'static' / 'data' / dataname
        result = makepath(pathstr, *args)
        createdirectory(result)


def makestructure(*args):
    data_recipedirectory(*args)
    model_recipedirectory(*args)


# data dir > recipe 내용
def data_recipedirectory(*args):
    data = datalist()
    for one in data:
        pathstr = Path(BASE_DIR) / 'static' / 'data' / one
        result = makepath(pathstr, *args)

        recipe = data_recipelist()
        for dirname in recipe:
            pathstr = result / dirname
            try:
                os.makedirs(pathstr)
            except OSError:
                print('Error: Failed to data_recipe create' + str(OSError))


# model dir > recipe 내용
def model_recipedirectory(*args):
    solution = solutionlist()
    for one in solution:
        pathstr = Path(BASE_DIR) / 'static' / 'ai_model' / one
        result = makepath(pathstr, *args)

        recipe = model_recipelist()
        for dirname in recipe:
            pathstr = result / dirname
            try:
                os.makedirs(pathstr)
            except OSError:
                print('Error: Failed to data_recipe create' + str(OSError))


# 기초코드를 경로로 변환
def makepath(pathstr, *args):
    pathstr = Path(pathstr)
    for one in args:
        pathstr = pathstr / one
    return pathstr


# 데이터 리스트 제어
def datalist():
    data = [
        'sensor',
        'wafermap',
    ]
    return data


# 솔루션 리스트 제어
def solutionlist():
    solution = ['anomaly', 'condition', 'discrepancy', 'vision', 'tracking']
    return solution


# data 레시피 내부 리스트 제어
def data_recipelist():
    recipe = ['raw_data', 'raw_data_csv', 'train_data', 'test_data', 'monitoring']
    return recipe


# model 레시피 내부 리스트 제어
def model_recipelist():
    recipe = ['model', 'results']
    return recipe


# 디렉토리 생성
def createdirectory(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        print('Error : Failed to create' + str(OSError))


# 모델 내부 버전
def versiondir(*args, revision):
    solution = solutionlist()
    revision = 'version_' + str(revision).zfill(2)
    for one in solution:
        pathstr = Path(BASE_DIR) / 'static' / 'ai_model' / one
        resultstr = makepath(pathstr, *args)
        result = resultstr / 'model' / revision
        try:
            os.makedirs(result)
        except OSError:
            print('Error: Failed to version dir create' + str(OSError))


# 파일 사이즈 측정
def get_dir_size(path):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total

