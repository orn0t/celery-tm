import time
import tempfile
import json
import unittest

from flask.testing import FlaskClient
from app import app

from models import db, TaskModel

class TestClient(FlaskClient):
    def open(self, *args, **kwargs):
        if 'json' in kwargs:
            kwargs['data'] = json.dumps(kwargs.pop('json'))
            kwargs['content_type'] = 'application/json'

        return super(TestClient, self).open(*args, **kwargs)


class APITestCase(unittest.TestCase):
    def setUp(self):
        app.testing = True
        app.test_client_class = TestClient
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + tempfile.mktemp()

        db.create_all()

        self.app = app.test_client()

    def tearDown(self):
        db.drop_all()

    """ Testing tasks scheduling endpoint """

    def test_cant_add_no_body_task(self):
        res = self.app.post('/api/v1.0/schedule')
        assert res.status_code == 400

    def test_cant_add_empty_task(self):
        res = self.app.post('/api/v1.0/schedule', json={})
        assert res.status_code == 400

    def test_cant_add_task_with_empty_schedule(self):
        res = self.app.post('/api/v1.0/schedule', json={'function': 'time.time'})
        assert res.status_code == 400

    def test_cant_add_task_with_empty_function(self):
        res = self.app.post('/api/v1.0/schedule', json={'schedule': '1 * * * *'})
        assert res.status_code == 400

    def test_can_add_task_without_arguments(self):
        res = self.app.post('/api/v1.0/schedule', json={'schedule': '1 * * * *', 'function': 'time.time'})
        assert res.status_code == 201

    def test_can_add_task_with_positioned_arguments(self):
        res = self.app.post('/api/v1.0/schedule', json={'schedule': 10, 'function': 'operator.add', 'args': [1, 2]})
        assert res.status_code == 201

    """ Testing tasks removing endpoint """

    def test_cant_remove_task_with_wrong_id(self):
        res = self.app.delete('/api/v1.0/schedule', json={'id': 9999})
        assert res.status_code == 404

    def test_can_remove_task_by_id(self):
        task = TaskModel({'function': 'time.time', 'schedule': '1 * * * *'})
        db.session.add(task)
        db.session.commit()

        res = self.app.delete('/api/v1.0/schedule', json={'id': task.id})
        assert res.status_code == 204


    """ Testing last_update endpoint """

    def test_update_endpoint_is_reachable(self):
        res = self.app.get('/api/v1.0/last_update')
        assert res.status_code == 200

    def test_update_endpoint_timestamp_present(self):
        res = self.app.get('/api/v1.0/last_update')
        j = json.loads(res.data)

        assert 'date' in j.keys()

    def test_update_endpoint_timestamp_was_changed_after_task_created(self):
        res = self.app.get('/api/v1.0/last_update')
        j = json.loads(res.data)
        old_date = j['date']

        # waiting before adding a task
        time.sleep(1)

        self.app.post('/api/v1.0/schedule', json={'schedule': '1 * * * *', 'function': 'time.time'})
        res = self.app.get('/api/v1.0/last_update')
        j = json.loads(res.data)

        assert j['date'] > old_date

    def test_update_endpoint_timestamp_was_changed_after_task_removed(self):
        task = TaskModel({'function': 'time.time', 'schedule': '1 * * * *'})
        db.session.add(task)
        db.session.commit()

        res = self.app.get('/api/v1.0/last_update')
        j = json.loads(res.data)
        old_date = j['date']

        # waiting before deleting task
        time.sleep(1)

        # weird but we need to reconcile object for some reasons
        task = db.session.merge(task)

        self.app.delete('/api/v1.0/schedule', json={'id': task.id})
        res = self.app.get('/api/v1.0/last_update')
        j = json.loads(res.data)

        assert j['date'] > old_date