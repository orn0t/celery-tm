import json
from flask_sqlalchemy import SQLAlchemy

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
    run_type = db.Column(db.String(32))
    schedule = db.Column(db.String(64))
    args = db.Column(db.Text)
    last_run = db.Column(db.String(32))
    exit_code = db.Column(db.String(64))
    # @todo: find out how to save uuid in more proper way
    uuid = db.Column(db.String(64))

    def __init__(self, data):
        self.function = data['function']
        self.run_type = ''
        self.schedule = data['schedule']

        if 'args' in data.keys():
            self.args = json.dumps(data['args'])

class LogItemModel(db.Model, BaseModel):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=db.func.now())
