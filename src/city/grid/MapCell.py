from src.common.Location import Location


class MapCell:
    def __init__(self, x, y, location=Location):
        self.x = x
        self.y = y
        self.rss = 0
        self.location = location
