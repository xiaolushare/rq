from tests import RQTestCase

from rq.queue import Queue
from rq.results import Result, get_key

from .fixtures import say_hello


class TestScheduledJobRegistry(RQTestCase):

    def test_save_and_get_result(self):
        """Ensure data is saved properly"""
        queue = Queue(connection=self.connection)
        job = queue.enqueue(say_hello)

        result = Result.get_latest(job.id, self.connection)
        self.assertIsNone(result)

        Result.create(job, Result.Type.SUCCESSFUL, ttl=10, return_value=1)
        result = Result.get_latest(job.id, self.connection)
        self.assertEqual(result.return_value, 1)
        self.assertEqual(job.get_latest_result().return_value, 1)

        # Check that ttl is properly set
        key = get_key(job.id)
        ttl = self.connection.pttl(key)
        self.assertTrue(5000 < ttl <= 10000)

        # Check job with None return value
        Result.create(job, Result.Type.SUCCESSFUL, ttl=10, return_value=None)
        result = Result.get_latest(job.id, self.connection)
        self.assertIsNone(result.return_value)
        Result.create(job, Result.Type.SUCCESSFUL, ttl=10, return_value=2)
        result = Result.get_latest(job.id, self.connection)
        self.assertEqual(result.return_value, 2)

    def test_create_failure(self):
        """Ensure data is saved properly"""
        queue = Queue(connection=self.connection)
        job = queue.enqueue(say_hello)
        Result.create_failure(job, ttl=10, exc_string='exception')
        result = Result.get_latest(job.id, self.connection)
        self.assertEqual(result.exc_string, 'exception')

        # Check that ttl is properly set
        key = get_key(job.id)
        ttl = self.connection.pttl(key)
        self.assertTrue(5000 < ttl <= 10000)

    def test_getting_results(self):
        """Check getting all execution results"""
        queue = Queue(connection=self.connection)
        job = queue.enqueue(say_hello)
        result_1 = Result.create_failure(job, ttl=10, exc_string='exception')
        result_2 = Result.create(job, Result.Type.SUCCESSFUL, ttl=10, return_value=1)
        result_3 = Result.create(job, Result.Type.SUCCESSFUL, ttl=10, return_value=1)

        # Result.get_latest() returns the latest result
        result = Result.get_latest(job, self.connection)
        self.assertEqual(result, result_3)

        # Result.all() returns all results, newest first
        results = Result.all(job, self.connection)
        self.assertEqual(results, [result_3, result_2, result_1])
