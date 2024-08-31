import numpy as np

class PositionModel():
    def __init__(self, x_position, y_position):
        self.x_coord = x_position
        self.y_coord = y_position

    def calculate_distance(self, c_position):
        x1 = self.x_coord
        y1 = self.y_coord
        x2 = c_position.x_coord
        y2 = c_position.y_coord
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)