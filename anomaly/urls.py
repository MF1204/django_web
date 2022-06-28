from django.urls import path
from .anomaly_views import monitoring_views, training_views, analysis_views, datasetup_views
from .anomaly_views import grid_views, old_upload_views, old_training_views, old_monitoring_views

app_name = 'anomaly'

urlpatterns = [
    # data setup
    path('uploaddata', old_upload_views.DataUploadView.as_view(), name='uploaddata'),
    path('datasetup/', datasetup_views.DataSetupView.as_view(), name='datasetup'),
    path('rawconvert/', datasetup_views.RawConvert.as_view(), name='rawconvert'),
    path('datalist/', datasetup_views.Datalist.as_view(), name='datalist'),
    path('search/', datasetup_views.Search.as_view(), name='Search'),
    path('setdata/', datasetup_views.SetData.as_view(), name='setdata'),

    # training
    path('training/', training_views.training_main, name='training'),
    path('training_start/', training_views.training_start, name='training_start'),
    path('training_graph/', training_views.training_graph, name='training_graph'),
    path('get-csv-size/', training_views.get_data_size, name='get-csv-size'),

    # monitoring
    path('monitoring/', monitoring_views.Monitoring.as_view(), name='monitoring'),
    path('monitoring_start/', monitoring_views.monitoring_start, name='monitoring_start'),
    path('monitoring_stop/', monitoring_views.monitoring_stop, name='monitoring_stop'),

    path('old_monitoring/', old_monitoring_views.monitoringmain.as_view(), name='monitoringmain'),
    path('old_monitoring/execute', old_monitoring_views.execute_monitoring.as_view(), name='execute_monitoring'),
    path('old_monitoring/find_chamber', old_monitoring_views.find_chamber.as_view(), name='find_chamber'),
    path('old_monitoring/find_recipe', old_monitoring_views.find_recipe.as_view(), name='find_recipe'),
    path('old_monitoring/find_revision', old_monitoring_views.find_revision.as_view(), name='find_revision'),
    path('old_monitoring/find_sensor', old_monitoring_views.find_sensor.as_view(), name='find_sensor'),
    path('old_monitoring/run_monitoring', old_monitoring_views.run_monitoring.as_view(), name='run_monitoring'),
    path('old_monitoring/upload', old_monitoring_views.monitoring_upload.as_view(), name='old_monitoring_upload'),
    path('old_monitoring/stop_thread', old_monitoring_views.stop_thread.as_view(), name='stop_thread'),

    # analysis
    path('analysis/', analysis_views.analysis_main.as_view(), name='analysis'),
]