# Creating tasks

Each task must be described using default Celery `@task` decorator

```python
@app.task
def first():
    print "first bar"
    return True
```

Tasks must be stored inside `tasks` directory on same level with `worker.py` to be autoloaded

Otherwise you must provide `CELERY_TM_TASKS` environment variable for tasks path

# Running worker

By default worker uses Redis on `redis://localhost:6379/0` as tasks broker 

You may use `CELERY_TM_BROKER` environment variable to override this setting

If you have some time-zone sensitive routines check `CELERY_TM_TIMEZONE` it uses `Europe/Kiev` by default

You can run the worker by executing our program with the `worker` argument

`celery -A worker worker --loglevel=info`

Or check http://docs.celeryproject.org/en/latest/userguide/daemonizing.html if you need to run as demon 

# Running beat

Beat is designed for getting periodic tasks from API service and putting them onto celery broker

Check `CELERY_TM_BROKER`, `CELERY_TM_TIMEZONE` variables according to your `worker` configuration 

And set proper `CELERY_TM_TASKS_URL` pointing to API endpoint (http://127.0.0.1:5000/api/v.0.1/pool by default)

Then use `beat` argument to run or look for http://docs.celeryproject.org/en/latest/userguide/daemonizing.html

`celery -A beat beat --loglevel=info`