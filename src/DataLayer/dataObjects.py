class ScConfig:
    def __init__(self):
        self.width: int # deg
        self.tilt: int
        self.startDepth: float # mm
        self.endDepth: float # mm
        self.numSamplesDrOut: int