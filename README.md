Installation 
------------

###### Get latest sources from GitHub

```bash
git clone git://github.com/orn0t/celery-tm.git
```

###### Install project dependencies 

```bash
cd celety-tm

pip install -r requirements.txt
```

###### Install and run message queue for Celery - Redis or RabbitMQ
 
If you are using Centos7:
```bash
wget http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-5.noarch.rpm

sudo rpm -ivh epel-release-7-5.noarch.rpm

sudo yum -y updates
sudo yum install redis -y

sudo systemctl start redis.service
``` 
 
Or even on MacOS:
```bash
brew install redis

# starting on system load, not necessary:  
ln -sfv /usr/local/opt/redis/*.plist ~/Library/LaunchAgents

launchctl load ~/Library/LaunchAgents/homebrew.mxcl.redis.plist
```


Configuration
--------------

Check `settings.py` for parameters you need:
  
```python
# Web API configuration
CELERY_TM_API_HOST = '127.0.0.1'
CELERY_TM_API_PORT = 5000

# Task schedule configuration
CELERY_TM_BROKER = 'redis://localhost:6379/0'
CELERY_TM_TIMEZONE = 'Europe/Kiev'
```

Running application
-------------------



Using REST API for task management
----------------------------------
 
#### Adding new task that runs immediately and only once  
 
```json
POST /api/v.0.1/task

{
  "name": "tasks.module.task_name",
  "description": "human readable task name",
  "run_type": "once",
  "schedule": "now"
}
```

#### Adding scheduled single-time task

```json
POST /api/v.0.1/task

{
  "name": "tasks.module.task_name",
  "description": "human readable task name",
  "run_type": "once",
  "schedule": __int__timespamp_in_future__
}
```

#### Adding scheduled recurring task using cron-like syntax

```json
POST /api/v.0.1/task

{
  "name": "tasks.module.task_name",
  "description": "human readable task name",
  "run_type": "recurring",
  "schedule": "*/4 * * * *"
}
```

#### Adding scheduled recurring task with simple fixed interval in seconds

```json
POST /api/v.0.1/task

{
  "name": "tasks.module.task_name",
  "description": "human readable task name",
  "run_type": "recurring",
  "schedule": 3000
}
```

#### Removing task

```
DELETE /api/v.0.1/task/<int: task_id>
```

#### List all tasks

```
GET /api/v.0.1/tasks
```