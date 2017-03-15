#!/usr/bin/python
# -*- coding: utf-8 -*-
import time

from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse, marshal_with, fields

from sqlalchemy import func

from celery import Celery
from models import db, TaskModel, UpdatesModel

import settings

cel = Celery(__name__, broker=settings.CELERY_TM_BROKER)

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
        parser.add_argument('recurring', type=int, required=False)
        args = parser.parse_args()

        for k in args.keys():
            if args[k] == None:
                args.pop(k)

        if fields:
            tasks = TaskModel.query.filter_by(**args).all()
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
        if 'now' == schedule['schedule']:
            uuid = cel.send_task('worker.dynamicTask', kwargs={'taskname': schedule.function, 'taskargs': schedule.args})
        elif schedule['schedule'].isdigit():
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
        args = parser.parse_args()

        if TaskModel.query.filter_by(**args).delete():
            db.session.commit()
            return '', 204

        return '', 404


@app.route('/api/v1.0/last_update')
def last_update():
    update = UpdatesModel.query.filter_by(id=1).first()

    return jsonify(update.as_dict())


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
    app.run(host=settings.CELERY_TM_API_HOST, port=settings.CELERY_TM_API_PORT)
