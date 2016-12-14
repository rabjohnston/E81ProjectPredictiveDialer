from unittest import TestCase
from calling_list import CallingList

FILENAME = '../test.csv'


class TestCallingList(TestCase):

    def test_load(self):
        cl = CallingList()
        self.assertEqual(len(cl._df), 0)

        cl.load(FILENAME)

        self.assertGreater(len(cl._df), 0)


    def test_parse(self):
        cl = CallingList()
        cl.load(FILENAME)
        cl.parse()
        self.assertEquals(len(cl._calls), 100)

        first_call = cl._calls[0]
        self.assertEqual(first_call.unique_id, '0cb53c48fef5cdd7:a1aa85:142e53206f3:-7fb6')

        last_call = cl._calls[99]
        self.assertEqual(last_call.unique_id, '0cb53c48fef5cdd7:1e29b99:1439ecae6c3:-3d3a')


    def test_get_call(self):
        cl = CallingList()
        cl.load(FILENAME)
        cl.parse()
        self.assertEquals(len(cl._calls), 100)

        first_call_peeked = cl._calls[0]
        self.assertEqual(first_call_peeked.unique_id, '0cb53c48fef5cdd7:a1aa85:142e53206f3:-7fb6')

        first_call_get = cl.get_call()
        self.assertEqual(first_call_get.unique_id, '0cb53c48fef5cdd7:a1aa85:142e53206f3:-7fb6')

        # The second call should now be at the top
        second_call_peeked = cl._calls[0]
        self.assertEqual(second_call_peeked.unique_id, '0cb53c48fef5cdd7:a1aa85:142e53206f3:-7fb5')

        self.assertEqual(len(cl._calls), 99)



    def test_get_queued_call(self):
        cl = CallingList()
        cl.load(FILENAME)
        cl.parse()
        self.assertEquals(len(cl._queued_calls), 15)

        first_call_peeked = cl._queued_calls[0]
        self.assertEqual(first_call_peeked.unique_id, '0cb53c48fef5cdd7:a1aa85:142e53206f3:-7f98')

        first_call_get = cl.get_queued_call()
        self.assertEqual(first_call_get.unique_id, '0cb53c48fef5cdd7:a1aa85:142e53206f3:-7f98')

        # The second call should now be at the top
        second_call_get = cl.get_queued_call()
        self.assertEqual(second_call_get.unique_id, '0cb53c48fef5cdd7:a1aa85:142e53206f3:-7f71')

