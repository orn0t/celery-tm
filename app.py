#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

import os

from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import  Column, Integer, String, DateTime, func, Text, event

from celery import Celery

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
api = Api(app)

db = SQLAlchemy(app)

# @todo: extract to app env/arguments
app.debug = True

# @todo: extract to app env/arguments
cel = Celery(__name__, broker='redis://localhost:6379/0')


""" Databese Models """

# @todo: extract
class BaseModel:
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# @todo: extract to models
# @todo: add proper fields validation
class TaskModel(db.Model, BaseModel):
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
    def __init__(self, data):
        self.name = data.function
        self.run_type = ''
        self.description = ''
        self.schedule = data.schedule

        if 'args' in data.keys():
            self.args = jsonify(data.args)


class LogItemModel(db.Model, BaseModel):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())


class UpdatesModel(db.Model, BaseModel):
    __tablename__ = 'updates'

    id = Column(Integer, primary_key=True)
    date = Column(Integer, default=0)

    def __init__(self, date):
        self.date = date


@event.listens_for(UpdatesModel.__table__, 'after_create')
def insert_default_updater_record(*args, **kwargs):
    db.session.add(UpdatesModel(int(time.time())))
    db.session.commit()

db.create_all()

@app.teardown_request
def teardown_request(exception):
    db.session.remove()

""" Application routes """

class Schedule(Resource):
    def __init__(self):
        self.schedule_parser = reqparse.RequestParser()
        self.schedule_parser.add_argument('function', type=str, required=True, location='json')
        self.schedule_parser.add_argument('schedule', type=str, required=True, location='json')
        self.schedule_parser.add_argument('args', type=list, location='json')

    def post(self):
        schedule = self.schedule_parser.parse_args()

        if 'now' == schedule.schedule:
            uuid = cel.send_task('worker.dynamicTask', kwargs={'taskname': schedule.function, 'taskargs': schedule.args})
        elif schedule.schedule.isdigit():
            time_now = time.time()
            time_gap = (int(schedule.schedule) - time_now) / 1000

            uuid = cel.send_task('worker.dynamicTask', kwargs={'taskname': schedule.function, 'taskargs': schedule.args}, countdown=time_gap)

        task = TaskModel(schedule)
        task.uuid = uuid

        db.session.add(task)
        db.session.query(UpdatesModel).filter_by(id=1).update({'date': int(time.time())})
        db.session.commit()

        return 'TASK_ADDED: %d' % task.id, 200

@app.route('/api/v1.0/task/<int:task_id>', methods=['GET', 'PATCH', 'DELETE'])
def act_task(task_id):

    if 'DELETE' == request.method:
        if TaskModel.query.filter_by(id=task_id).delete():

            # @todo: revoke/remove task from celery queue!
            db.session.commit()
            db.session.query(UpdatesModel).filter_by(id=1).update({'date': int(time.time())})
            db.session.commit()

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


@app.route('/api/v1.0/tasks', methods=['GET'])
def tasks():
    all_tasks = TaskModel.query.all()

    return jsonify([t.as_dict() for t in all_tasks])


@app.route('/api/v1.0/last_update')
def last_update():
    update = UpdatesModel.query.filter_by(id=1).first()

    return jsonify(update.as_dict())


@app.route('/api/v1.0/pool', methods=['GET'])
def pool():
    all_tasks = TaskModel.query.filter_by(run_type='recurring').all()

    return jsonify([t.as_dict() for t in all_tasks])


@app.route('/api/v1.0/log', methods=['GET', 'POST'])
def log():
    pass


@app.route('/api/v1.0/result/<uuid>', methods=['POST'])
def result(uuid):
    task = TaskModel.query.filter_by(uuid=uuid).first()

    if task:
        task.last_run = func.now()
    else:
        return 'TASK_NOT_FOUND: %s' % uuid, 404

    return 'OK', 200


api.add_resource(Schedule, '/api/v1.0/schedule')

if __name__ == "__main__":
    # @todo: configure host/port from env
    APP_HOST = os.getenv('CELERY_TM_API_HOST', '127.0.0.1')
    APP_PORT = os.getenv('CELERY_TM_API_PORT', 5000)
    app.run(host=APP_HOST, port=APP_PORT)
