#!/usr/bin/python
# -*- coding: utf-8 -*-

import importlib
from celery import Celery, signals

import settings

app = Celery(__name__, broker=settings.CELERY_TM_BROKER)
app.conf.timezone = settings.CELERY_TM_TIMEZONE


@app.task
def dynamicTask(taskname, taskargs):
    # We cant load function directly, so splitting name
    modulename, funcname = taskname.rsplit('.', 1)

    module = importlib.import_module(modulename)
    func = getattr(module, funcname)

    print taskname, taskargs

    # arguments can be proceed as positional list or key-value
    if not taskargs:
        return func()
    if isinstance(taskargs, dict):
        return func(**taskargs)
    elif isinstance(taskargs, list):
        return func(*taskargs)


@app.on_after_configure.connect
def after_configure(**kwargs):
    pass


@signals.task_success.connect
def task_success(**kwargs):
    pass


@signals.task_failure.connect
def task_success(**kwargs):
    pass