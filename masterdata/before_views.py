from django.shortcuts import render
from django.views.generic import View
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from config.models import mmRecipe, mmProblem, mmDataset
from django.db import transaction
import json


class masterdatamain(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        return render(request, 'masterdata/masterdatamain.html', context)


def recipe(request):
    context = {}

    RecipeDataList = mmRecipe.objects.filter
    context['RecipeDataList'] = RecipeDataList

    return render(request, 'masterdata/recipe.html', context)


def problem(request):
    context = {}

    ProblemDataList = mmProblem.objects.filter
    context['ProblemDataList'] = ProblemDataList

    return render(request, 'masterdata/problem.html', context)


def dataset(request):
    context = {}

    DataSetList = mmDataset.objects.filter
    context['DataSetList'] = DataSetList

    return render(request, 'masterdata/dataset.html', context)


class masterdatarecipefind(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        data = mmRecipe.objects.all()
        print(data.values())
        context['data'] = list(data.values())

        return JsonResponse(context, content_type='application/json')


class masterdataproblemfind(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        data = mmProblem.objects.all()
        print(data.values())
        context['data'] = list(data.values())

        return JsonResponse(context, content_type='application/json')


class masterdatadatasetfind(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        data = mmDataset.objects.all()
        print(data.values())
        context['data'] = list(data.values())

        return JsonResponse(context, content_type='application/json')


class recipedatainsert(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        return render(request, 'masterdata/recipedatainsert.html', context)


class insert_recipe(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        try:
            with transaction.atomic():
                mmRecipe.objects.create(
                    recipe_id=request.POST['recipe_id'],
                    recipe_name=request.POST['recipe_name'],
                    revision_no=request.POST['revision_no'],
                    equip_name=request.POST['equip_name'],
                    chamber_name=request.POST['chamber_name'],
                    sensor_cd=request.POST['sensor_cd'],
                    sensor_name=request.POST['sensor_name']
                )
        except:
            context['success'] = False
            context['message'] = "저장에 실패하였습니다."
            return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['message'] = "저장되었습니다."

        return JsonResponse(context, content_type='application/json')


class recipedatamodify(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        id = request.GET['id']
        data = mmRecipe.objects.get(id=id)

        context = {
            'data': data
        }

        return render(request, 'masterdata/recipedatamodify.html', context)


class update_recipe(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        id = request.POST['id']

        try:
            with transaction.atomic():
                data = mmRecipe.objects.get(id=id)
                data.recipe_id = request.POST['recipe_id']
                data.recipe_name = request.POST['recipe_name']
                data.revision_no = request.POST['revision_no']
                data.equip_name = request.POST['equip_name']
                data.chamber_name = request.POST['chamber_name']
                data.sensor_cd = request.POST['sensor_cd']
                data.sensor_name = request.POST['sensor_name']
                data.save()
        except:
            context['success'] = False
            context['message'] = "수정에 실패하였습니다."
            return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['message'] = "수정되었습니다."

        return JsonResponse(context, content_type='application/json')


class delete_recipe(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        rsData = json.loads(request.body.decode("utf-8"))
        print("rsData::::", rsData)

        # id = request.POST['id']

        try:
            with transaction.atomic():
                data = mmRecipe.objects.get(id=id)
                data.delete()
        except:
            context['success'] = False
            context['message'] = "삭제에 실패하였습니다."
            return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['message'] = "삭제되었습니다."

        return JsonResponse(context, content_type='application/json')


class problemdatamodify(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        id = request.GET['id']
        data = mmProblem.objects.get(id=id)

        context = {
            'data': data
        }

        return render(request, 'masterdata/problemmodify.html', context)


class update_problem(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        id = request.POST['id']
        problem_name = request.POST['problem_name']
        problem_note = request.POST['problem_note']

        try:
            with transaction.atomic():
                data = mmProblem.objects.get(id=id)
                data.problem_name = problem_name
                data.problem_note = problem_note
                data.save()
        except:
            context['success'] = False
            context['message'] = "수정에 실패하였습니다."
            return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['message'] = "수정되었습니다."

        return JsonResponse(context, content_type='application/json')


class delete_problem(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        id = request.POST['id']

        try:
            with transaction.atomic():
                data = mmProblem.objects.get(id=id)
                data.delete()
        except:
            context['success'] = False
            context['message'] = "삭제에 실패하였습니다."
            return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['message'] = "삭제되었습니다."

        return JsonResponse(context, content_type='application/json')


class datasetdatamodify(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        context = {}

        id = request.GET['id']
        data = mmDataset.objects.get(id=id)

        context = {
            'data': data
        }

        return render(request, 'masterdata/datasetmodify.html', context)


class update_dataset(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        id = request.POST['id']

        try:
            with transaction.atomic():
                data = mmDataset.objects.get(id=id)
                data.equip_name = request.POST['equip_name']
                data.chamber_name = request.POST['chamber_name']
                data.recipe_name = request.POST['recipe_name']
                data.data_static_path = request.POST['data_static_path']
                data.purpose = request.POST['purpose']
                data.data_name = request.POST['data_name']
                data.save()
        except:
            context['success'] = False
            context['message'] = "수정에 실패하였습니다."
            return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['message'] = "수정되었습니다."

        return JsonResponse(context, content_type='application/json')


class delete_dataset(View):
    def post(self, request: HttpRequest, *args, **kwargs):
        context = {}

        id = request.POST['id']

        try:
            with transaction.atomic():
                data = mmDataset.objects.get(id=id)
                data.delete()
        except:
            context['success'] = False
            context['message'] = "삭제에 실패하였습니다."
            return JsonResponse(context, content_type='application/json')

        context['success'] = True
        context['message'] = "삭제되었습니다."

        return JsonResponse(context, content_type='application/json')

