#!/usr/bin/python
# -*- coding: utf-8 -*-
from celery import Celery

app = Celery('manager', broker="redis://localhost:6379/0")

@app.task
def alpha():
    print 'alpha task'

@app.task
def beta():
    print 'beta task'

@app.task
def theta():
    print 'theta task'
    return 3
