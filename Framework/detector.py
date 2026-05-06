class Detector:
    def __init__(self, comparator, percentile, consecutive_required):
        self.comparator = comparator
        self.percentile = percentile
        self.consecutive_required = consecutive_required

    def detect(self, distances, threshold):

        exceed = distances > threshold

        current = 0

        for x in exceed:
            if x:
                current += 1
                if current >= self.consecutive_required:
                    return True
            else:
                current = 0

        return False