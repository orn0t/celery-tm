import os
import json
import unittest

from flask.testing import FlaskClient
import app as celery_tm


class TestClient(FlaskClient):
    def open(self, *args, **kwargs):
        if 'json' in kwargs:
            kwargs['data'] = json.dumps(kwargs.pop('json'))
            kwargs['content_type'] = 'application/json'

        return super(TestClient, self).open(*args, **kwargs)


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = celery_tm.app.test_client()

    def test_cant_add_empty_task(self):
        res = self.app.post('/api/v1.0/schedule')
        assert res.status_code == 400