from src.utils.thread_safe_data import ThreadSafeData
import unittest

class TestThreadSafeData(unittest.TestCase):
    def setUp(self):
        self.thread_safe_data = ThreadSafeData()

    def test_set_and_get_data(self):
        self.thread_safe_data.set_data('key1', 'value1')
        self.assertEqual(self.thread_safe_data.get_data('key1'), 'value1')

    def test_get_non_existent_data(self):
        self.assertIsNone(self.thread_safe_data.get_data('non_existent_key'))

    def test_get_all_data(self):
        self.thread_safe_data.set_data('key1', 'value1')
        self.thread_safe_data.set_data('key2', 'value2')
        all_data = self.thread_safe_data.get_all_data()
        self.assertEqual(all_data, {'key1': 'value1', 'key2': 'value2'})

    def test_thread_safety(self):
        import threading

        def set_data_in_thread(key, value):
            self.thread_safe_data.set_data(key, value)

        threads = []
        for i in range(10):
            thread = threading.Thread(target=set_data_in_thread, args=(f'key{i}', f'value{i}'))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        all_data = self.thread_safe_data.get_all_data()
        self.assertEqual(len(all_data), 10)

if __name__ == '__main__':
    unittest.main()