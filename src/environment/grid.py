class Grid:
    def __init__(self, max_x, max_y):
        self.max_x = max_x
        self.max_y = max_y
        self.dangerous = set()

    def set_dangerous(self, x, y):
        if self.is_valid(x, y):
            self.dangerous.add((x, y))

    def is_valid(self, x, y):
        return 0 <= x <= self.max_x and 0 <= y <= self.max_y

    def is_dangerous(self, x, y):
        return (x, y) in self.dangerous

    def zoneOf(self, x, y):
        mid_x = self.max_x // 2
        mid_y = self.max_y // 2

        if x <= mid_x and y <= mid_y:
            return 1
        if x <= mid_x and y > mid_y:
            return 2
        if x > mid_x and y <= mid_y:
            return 3
        return 4

    def neighbors(self, x, y):
        candidates = [
            (x, y + 1),
            (x, y - 1),
            (x + 1, y),
            (x - 1, y),
        ]
        return [(nx, ny) for nx, ny in candidates if self.is_valid(nx, ny)]