class Detector:

    """
    INPUT:
        consecutive maximum concept discrepancies

    OUTPUT:
        drift or no drift flagging
    """

    def __init__(self, comparator, percentile, consecutiveRequired):

        self.comparator = comparator
        self.percentile = percentile
        self.consecutiveRequired = consecutiveRequired

    # Detect drift based on consecutive threshold violations
    def detect(self, distances, threshold):

        exceedsThreshold = distances > threshold
        consecutiveCount = 0

        for distanceExceeded in exceedsThreshold:

            if distanceExceeded:

                consecutiveCount += 1

                if consecutiveCount >= self.consecutiveRequired:
                    return True

            else:
                consecutiveCount = 0

        return False