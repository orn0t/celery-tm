#!/usr/bin/python
# -*- coding: utf-8 -*-
from celery import Celery

app = Celery('manager', broker="redis://localhost:6379/0")

@app.task
def first():
    print "first bar"
    return True


@app.task
def second():
    print "second bar"
    return True
