class Box:
    minX = None
    minY = None
    maxX = None
    maxY = None

    def centerX(self):
        return min(self.minX, self.maxX) + abs(self.minX - self.maxX)/2

    def centerY(self):
        return min(self.minY, self.maxY) + abs(self.minY - self.maxY)/2

    def center(self):
        return (self.centerX(), self.centerY())

    def relativeX(self, x, range=100):
        if (self.minX == self.maxX):
            return range;
        return (self.maxX - x)/(self.maxX - self.minX) * range

    def relativeY(self, y, range=100):
        if (self.minY == self.maxY):
            return range;
        return (self.maxY - y)/(self.maxY - self.minY) * range

    def width(self):
        return abs(self.maxX - self.minX)

    def height(self):
        return abs(self.maxY - self.minY)

    def coords(self):
        return (self.minX, self.minY, self.maxX, self.maxY)
