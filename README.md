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

