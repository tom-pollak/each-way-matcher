class MatcherError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"ERROR Occurred: {self.message}"


import time


class TrackTime:
    def __init__(self, funtion_name):
        self.funtion_name = funtion_name
        self.start = time.time()

    def end(self):
        diff = round(time.time() - self.start)
        if diff > 60:
            print(f"{self.funtion_name} completed in {diff}")
