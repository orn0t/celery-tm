import unittest

import worker


class TestCeleryWorker(unittest.TestCase):
    def setUp(self):
        worker.app.conf.update(task_always_eager=True)

    def test_can_run_existing_function_without_args(self):
        res = worker.dynamicTask.delay('time.time')
        assert res.get() > 0

    def test_can_run_existing_function_with_args(self):
        res = worker.dynamicTask.delay('operator.add', [1, 2])
        assert res.get() == 3


