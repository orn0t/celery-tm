#!/usr/bin/python
# -*- coding: utf-8 -*-

import glob
from os.path import dirname, basename, isfile
from celery import Celery, signals

app = Celery(__name__, broker="redis://localhost:6379/0")
app.conf.timezone = 'Europe/Kiev'

# @todo: use app env/arguments to set the path
tasks = glob.glob(dirname(__file__) + '/tasks/*.py')

# @todo: unwrap the magic
app.conf.imports = ['tasks.' + basename(f)[:-3] for f in tasks if isfile(f) and f != '__init__']

@app.on_after_configure.connect
def after_configure(**kwargs):
    pass

