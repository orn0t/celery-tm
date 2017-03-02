#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from celery import Celery, signals
from celery.beat import Scheduler, ScheduleEntry
from celery.schedules import crontab
from requests import ConnectionError

app = Celery(__name__, broker="redis://localhost:6379/0")
app.conf.timezone = 'Europe/Kiev'
app.conf.beat_max_loop_interval = 10

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    # sender.add_periodic_task(10.0, app.signature('tasks.bar.first'), name='add every 10')
    pass

'''
        {
            u'celery.backend_cleanup': <ScheduleEntry: celery.backend_cleanup celery.backend_cleanup() <crontab: 0 4 * * * (m/h/d/dM/MY)>,
            u'add every 10': <ScheduleEntry: add every 10 tasks.bar.first() <freq: 10.00 seconds>
        }
'''

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
            # @todo: move to env/arguments
            r = requests.get('http://127.0.0.1:5000/api/v.0.1/poll')
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
