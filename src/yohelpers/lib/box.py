class Box:
    minX = None
    minY = None
    maxX = None
    maxY = None

    def relativeX(self, x, range=100):
        return (self.maxX - x)/(self.maxX - self.minX) * range

    def relativeY(self, y, range=100):
        return (self.maxY - y)/(self.maxY - self.minY) * range

    def width(self):
        return abs(self.maxX - self.minX)

    def height(self):
        return abs(self.maxY - self.minY)

    def coords(self):
        return (self.minX, self.minY, self.maxX, self.maxY)
