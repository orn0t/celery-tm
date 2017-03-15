#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import requests
from celery import Celery
from celery.beat import Scheduler
from celery.schedules import crontab
from requests import ConnectionError

import settings

app = Celery(__name__, broker=settings.CELERY_TM_BROKER)
app.conf.timezone = settings.CELERY_TM_TIMEZONE
app.conf.beat_max_loop_interval = 10


class DynamicScheduler(Scheduler):
    _store = {}
    _last_update = 0

    def __init__(self, *args, **kwargs):
        Scheduler.__init__(self, *args, **kwargs)

    def is_schedule_changed(self):
        # Checking remote timestamp that changing on each schedule modification
        try:
            updates_url = os.getenv('CELERY_TM_TASKS_URL', 'http://127.0.0.1:5000/api/v1.0/last_update')
            r = requests.get(updates_url)
            if r.status_code == 200:
                res = r.json()

                if int(res['date']) > self._last_update:
                    self._last_update = int(res['date'])
                    return True

        except ConnectionError:
            print ConnectionError

        return False

    def setup_schedule(self):
        self.sync()

    def get_schedule(self):
        return self._store

    def set_schedule(self, schedule):
        self._store = schedule

    @property
    def schedule(self):
        if self.is_schedule_changed():
            self.sync()

            self._heap = None

        return self._store

    def update_schedule(self):
        # Pooling remote for tasks list and converting them to proper Entry objects
        s = {}
        try:
            tasks_url = os.getenv('CELERY_TM_TASKS_URL', 'http://127.0.0.1:5000/api/v1.0/pool')
            r = requests.get(tasks_url)
            if r.status_code == 200:
                for task in r.json():
                    # We have two types of schedule notation - integer interval or crontab string
                    if task['schedule'].isdigit():
                        schedule = int(task['schedule'])
                    else:
                        [m, h, d, M, F] = task['schedule'].split(' ')
                        schedule = crontab(minute=m, hour=h, day_of_month=d, month_of_year=M, day_of_week=F)

                    # Creating task Entry
                    s[task['description']] = self._maybe_entry(task['description'], {
                        'task': 'worker.dynamicTask',
                        'kwargs': {
                            'taskname': task['name'],
                            'taskargs': task['args']
                        },
                        'schedule': schedule
                    })

        except ConnectionError:
            print ConnectionError

        return s

    def sync(self):
        self._store = self.update_schedule()

    @property
    def info(self):
        return '----> custom scheduler'

app.conf.beat_scheduler = DynamicScheduler
