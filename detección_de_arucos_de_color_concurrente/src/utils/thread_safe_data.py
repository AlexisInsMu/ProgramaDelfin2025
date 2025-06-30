from threading import Lock

class ThreadSafeData:
    def __init__(self):
        self.lock = Lock()
        self.data = {}

    def set_data(self, key, value):
        with self.lock:
            self.data[key] = value

    def get_data(self, key, default=None):
        with self.lock:
            return self.data.get(key, default)

    def get_all_data(self):
        with self.lock:
            return self.data.copy()