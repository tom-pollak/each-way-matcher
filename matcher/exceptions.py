class MatcherError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"\nERROR Occurred: {self.message}"
