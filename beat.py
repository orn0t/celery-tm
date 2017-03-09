#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import requests
from celery import Celery, signals
from celery.beat import Scheduler, ScheduleEntry
from celery.schedules import crontab
from requests import ConnectionError

tm_broker = os.getenv('CELERY_TM_BROKER', 'redis://localhost:6379/0')
app = Celery(__name__, broker=tm_broker)
app.conf.timezone = os.getenv('CELERY_TM_TIMEZONE', 'Europe/Kiev')
app.conf.beat_max_loop_interval = 10

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    pass


class DynamicScheduler(Scheduler):
    """Scheduler backed by :mod:`shelve` database."""

    _store = {}

    def __init__(self, *args, **kwargs):
        Scheduler.__init__(self, *args, **kwargs)

    def setup_schedule(self):
        self._store = {}
        self.install_default_entries(self.schedule)
        self.update_from_dict(self.app.conf.beat_schedule)
        self.sync()

    def get_schedule(self):
        return self._store

    def set_schedule(self, schedule):
        self._store = schedule

    @property
    def schedule(self):
        print 'schedule request'
        return self._store

    def schedule_changed(self):
        pass

    def all_as_schedule(self):
        s = {}
        try:
            tasks_url = os.getenv('CELERY_TM_TASKS_URL', 'http://127.0.0.1:5000/api/v.0.1/pool')
            r = requests.get(tasks_url)
            if r.status_code == 200:
                s = {}

                for task in r.json():
                    if task['schedule'].isdigit():
                        s[task['description']] = self._maybe_entry(task['description'], {
                            'task': task['name'],
                            'schedule': int(task['schedule'])
                        })

                    else:
                        [m, h, d, M, F] = task['schedule'].split(' ')

                        s[task['description']] = self._maybe_entry(task['description'], {
                            'task': task['name'],
                            'schedule': crontab(minute=m, hour=h, day_of_month=d, month_of_year=M, day_of_week=F)
                        })

        except ConnectionError:
            print ConnectionError

        return s

    def sync(self):
        self._store = self.all_as_schedule()
        print self._store
        print 'sync call'

    def close(self):
        self.sync()

    @property
    def info(self):
        return '----> custom scheduler'

app.conf.beat_scheduler = DynamicScheduler
