#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import os

from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse, marshal_with, fields

from sqlalchemy import func, event

from celery import Celery
from models import db, TaskModel, UpdatesModel

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
api = Api(app)

db.app = app
db.init_app(app)

db.create_all()

@app.teardown_request
def teardown_request(exception):
    db.session.remove()

""" Application routes """
class Schedule(Resource):
    schema = {'id': fields.Integer, 'created': fields.DateTime, 'function': fields.String, 'schedule': fields.String}

    @marshal_with(schema)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int, required=False)
        fields = parser.parse_args()

        if fields.id:
            tasks = TaskModel.query.filter_by(**fields).all()
        else:
            tasks = TaskModel.query.all()

        return tasks, 200

    @marshal_with(schema)
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('function', type=str, required=True, location='json')
        parser.add_argument('schedule', type=str, required=True, location='json')
        parser.add_argument('args', type=list, location='json')
        schedule = parser.parse_args()

        task = TaskModel(schedule)

        uuid = ''
        if 'now' == schedule.schedule:
            uuid = cel.send_task('worker.dynamicTask', kwargs={'taskname': schedule.function, 'taskargs': schedule.args})
        elif schedule.schedule.isdigit():
            time_now = time.time()
            time_gap = (int(schedule.schedule) - time_now) / 1000

            uuid = cel.send_task('worker.dynamicTask', kwargs={'taskname': schedule.function, 'taskargs': schedule.args}, countdown=time_gap)

        task.uuid = str(uuid)

        db.session.add(task)
        db.session.commit()

        if task.id:
            return task, 201

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int, location='json')
        fields = parser.parse_args()

        if TaskModel.query.filter_by(**fields).delete():
            db.session.commit()
            return '', 204
        else:
            return '', 404

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
