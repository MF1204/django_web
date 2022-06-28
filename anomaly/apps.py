import os
import random
import sys
import threading
from pathlib import Path
import numpy as np
import torch
from django.apps import AppConfig
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from anomaly_detection import choi_main_test, monitoring_data_gen
from config.settings import BASE_DIR


class SAnomalyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'anomaly'
