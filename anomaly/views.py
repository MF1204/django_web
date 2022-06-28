from config.models import *
import os
from django.apps import AppConfig
from pathlib import Path
import pandas as pd
from config.settings import BASE_DIR


def rawlist(path):
    rawdata = os.listdir(path)
    rawlist = []
    if len(rawdata) == 0:
        return rawlist
    for one in rawdata:
        # one = one.replace('_', '')
        # one = one.replace('.csv', '')
        rawlist.append(one)
    return rawlist


def get_treestructure():
    process_list = info_process.objects.filter(usage_flag=1).order_by('code').values_list('code', 'name').distinct()
    treedata = ""
    state_open = '{ "opened": true }'
    for i in process_list:
        i = list(i)
        line = f'"id":"{i[0]}", "parent":"#", "text":"{i[0]}:{i[1]}", "state" : {state_open}, "icon" : "jstree-folder"'
        treedata += '{' + line + '}, '
        equipment_list = info_equipment.objects.filter(process_id__code=i[0], usage_flag=1).order_by('code').values_list('code', 'name').distinct()
        for j in equipment_list:
            j = list(j)
            line = f'"id":"{j[0]}", "parent":"{i[0]}", "text":"{j[0]}:{j[1]}", "state" : {state_open}'
            treedata += '{' + line + '}, '
            chamber_list = info_chamber.objects.filter(equipment_id__code=j[0], usage_flag=1).order_by('code').values_list('code', 'name').distinct()
            for k in chamber_list:
                k = list(k)
                line = f'"id":"{k[0]}", "parent":"{j[0]}", "text":"{k[0]}:{k[1]}", "state": {state_open}'
                treedata += '{' + line + '}, '
                recipe_list = info_recipe.objects.filter(chamber_id__code=k[0], usage_flag=1).order_by('code').values_list('code', 'name').distinct()
                for recipe in recipe_list:
                    recipe = list(recipe)
                    line = f'"id":"{recipe[0]}", "parent":"{k[0]}", "text":"{recipe[0]}:{recipe[1]}", "state": {state_open}'
                    treedata += '{' + line + '}, '

    # print(treedata)
    treedata = treedata[:-2]
    treedata = '[' + treedata + ']'
    return treedata
