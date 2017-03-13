#!/usr/bin/python
# -*- coding: utf-8 -*-

import glob
import os
import importlib
from celery import Celery, signals


tm_broker = os.getenv('CELERY_TM_BROKER', 'redis://localhost:6379/0')
app = Celery(__name__, broker=tm_broker)
app.conf.timezone = os.getenv('CELERY_TM_TIMEZONE', 'Europe/Kiev')

tasks_path = os.getenv('CELERY_TM_TASKS', os.path.dirname(__file__) + '/tasks/*.py')
tasks = glob.glob(tasks_path)

# @todo: unwrap the magic
app.conf.imports = ['tasks.' + os.path.basename(f)[:-3] for f in tasks if os.path.isfile(f) and f != '__init__']

@app.on_after_configure.connect
def after_configure(**kwargs):
    pass

@signals.task_success.connect
def task_success(**kwargs):
    pass

@signals.task_failure.connect
def task_success(**kwargs):
    pass
