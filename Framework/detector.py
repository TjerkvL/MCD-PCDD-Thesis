class Detector:
    """
    INPUT:
        distances: List[Tensor]
        threshold: Tensor/float
    OUTPUT:
        bool drift
    """

    def __init__(self, comparator, percentile, consecutive_required):
        self.comparator = comparator
        self.percentile = percentile
        self.consecutive_required = consecutive_required
        self.counter = 0

    def detect(self, distances, threshold):
        if distances[-1] > threshold:
            self.counter += 1
        else:
            self.counter = 0

        return self.counter >= self.consecutive_required