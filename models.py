import json
import time
from sqlalchemy import event
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property

db = SQLAlchemy()

class BaseModel:
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class UpdatesModel(db.Model, BaseModel):
    __tablename__ = 'updates'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Integer, default=0)

    def __init__(self, date):
        self.date = date

# @todo: add proper fields validation
class TaskModel(db.Model, BaseModel):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=db.func.now())
    function = db.Column(db.String(64))
    args = db.Column(db.Text)
    last_run = db.Column(db.String(32))
    exit_code = db.Column(db.String(64))
    uuid = db.Column(db.String(64))
    recurring = db.Column('recurring', db.Integer, default=0)

    _schedule = db.Column('schedule', db.String(64))

    def __init__(self, data):
        self.function = data['function']
        self.schedule = data['schedule']

        if 'args' in data.keys():
            self.args = json.dumps(data['args'])

    @hybrid_property
    def schedule(self):
        return self._schedule

    @schedule.setter
    def schedule(self, schedule):
        self._schedule = schedule

        if schedule != 'now':
            self.recurring = 1


class LogItemModel(db.Model, BaseModel):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=db.func.now())


@event.listens_for(UpdatesModel.__table__, 'after_create')
def insert_default_updater_record(*args, **kwargs):
    db.session.add(UpdatesModel(int(time.time())))
    db.session.commit()


@event.listens_for(db.session, 'before_commit')
def update_timestamp(*args, **kwargs):
    db.session.query(UpdatesModel).filter_by(id=1).update({'date': int(time.time())})