#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

import os

from flask import Flask, request, jsonify

from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, Text, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from celery import Celery

app = Flask(__name__)

# @todo: extract to app env/arguments
app.debug = True

# @todo: extract to app env/arguments
cel = Celery(__name__, broker='redis://localhost:6379/0')

sql_engine = create_engine('sqlite:///tasks.db')
sql_session = scoped_session(sessionmaker(autocommit=False,
                                          autoflush=False,
                                          bind=sql_engine))

SQLModel = declarative_base()
SQLModel.query = sql_session.query_property()

# @todo: extract
class BaseModel:
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# @todo: extract to models
# @todo: add proper fields validation
class TaskModel(SQLModel, BaseModel):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    name = Column(String(64))
    # @todo: replace with enum
    run_type = Column(String(32))
    description = Column(String(64))
    schedule = Column(String(64))
    args = Column(Text)
    last_run = Column(String(32))
    exit_code = Column(String(64))
    # @todo: find out how to save uuid in more proper way
    uuid = Column(String(64))

    # @todo: encapsulate with setters
    def __init__(self, name, run_type, description, schedule, args):
        self.name = name
        self.run_type = run_type
        self.description = description
        self.schedule = schedule
        self.args = args


class LogItemModel(SQLModel, BaseModel):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())


class UpdatesModel(SQLModel, BaseModel):
    __tablename__ = 'updates'

    id = Column(Integer, primary_key=True)
    date = Column(Integer, default=0)

    def __init__(self, date):
        self.date = date


@event.listens_for(UpdatesModel.__table__, 'after_create')
def insert_default_updater_record(*args, **kwargs):
    sql_session.add(UpdatesModel(int(time.time())))
    sql_session.commit()

# @todo: look for some migration tools for updating schemas
SQLModel.metadata.create_all(sql_engine)


@app.teardown_request
def teardown_request(exception):
    sql_session.remove()


@app.route('/api/v.0.1/task', methods=['POST'])
def new_task():

    if not request.json:
        return 'INVALID_JSON_REQUEST', 400

    if request.json['args']:
        task_args = jsonify(request.json['args'])
    else:
        task_args = '[]'

    # @todo: add validation on JSON data
    # @todo: simplify creating models from JSON
    task = TaskModel(request.json['name'],
                     request.json['run_type'],
                     request.json['description'],
                     request.json['schedule'],
                     task_args)

    if 'once' == task.run_type:
        if 'now' == task.schedule:
            uuid = cel.send_task('worker.dynamicTask', kwargs={'taskname': task.name, 'taskargs': task.args})
            task.uuid = str(uuid)
        else:
            time_now = time.time()
            time_gap = (int(task.schedule) - time_now) / 1000

            # @todo: get/save unique task id
            cel.send_task('worker.dynamicTask', kwargs={'taskname': task.name, 'taskargs': task.args}, countdown=time_gap)

    sql_session.add(task)

    sql_session.query(UpdatesModel).filter_by(id=1).update({'date': int(time.time())})

    sql_session.commit()

    return 'TASK_ADDED: %d' % task.id, 200


@app.route('/api/v.0.1/task/<int:task_id>', methods=['GET', 'PATCH', 'DELETE'])
def act_task(task_id):

    if 'DELETE' == request.method:
        if TaskModel.query.filter_by(id=task_id).delete():

            # @todo: revoke/remove task from celery queue!
            sql_session.commit()

            sql_session.query(UpdatesModel).filter_by(id=1).update({'date': int(time.time())})

            sql_session.commit()

            return 'TASK_REMOVED: %d' % task_id, 200
        else:
            return 'TASK_NOT_FOUND: %d' % task_id, 404

    if 'GET' == request.method:
        task = TaskModel.query.filter_by(id=task_id).first()

        if task:
            return jsonify(task.as_dict()), 200
        else:
            return 'TASK_NOT_FOUND: %d' % task_id, 404

    if 'PATCH' == request.method:
        pass

    return 'INVALID REQUEST', 400


@app.route('/api/v.0.1/tasks', methods=['GET'])
def tasks():
    all_tasks = TaskModel.query.all()

    return jsonify([t.as_dict() for t in all_tasks])


@app.route('/api/v.0.1/last_update')
def last_update():
    update = UpdatesModel.query.filter_by(id=1).first()

    return jsonify(update.as_dict())


@app.route('/api/v.0.1/pool', methods=['GET'])
def pool():
    all_tasks = TaskModel.query.filter_by(run_type='recurring').all()

    return jsonify([t.as_dict() for t in all_tasks])


@app.route('/api/v.0.1/log', methods=['GET', 'POST'])
def log():
    pass


@app.route('/api/v.0.1/result/<uuid>', methods=['POST'])
def result(uuid):
    task = TaskModel.query.filter_by(uuid=uuid).first()

    if task:
        task.last_run = func.now()
    else:
        return 'TASK_NOT_FOUND: %s' % uuid, 404

    return 'OK', 200


if __name__ == "__main__":
    # @todo: configure host/port from env
    APP_HOST = os.getenv('CELERY_TM_API_HOST', '127.0.0.1')
    APP_PORT = os.getenv('CELERY_TM_API_PORT', 5000)
    app.run(host=APP_HOST, port=APP_PORT)
