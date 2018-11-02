import re

class Color:
    r = 0
    g = 0
    b = 0

    @staticmethod
    def FromRGB(rgb):
        c = Color()
        values = re.findall("[0-9a-f]{2}", rgb, re.IGNORECASE)
        c.r = int(values[0], 16)
        c.g = int(values[1], 16)
        c.b = int(values[2], 16)
        return c

    # hexa representation of RGB
    def rgb(self):
        return "#%.2X%.2X%.2X" % (self.r, self.g, self.b)

    # percentage representation of cmyk
    def cmyk(self):
        k = 0 # let's assume that there is no black left in printer
        c = int(100 * ((1 - (self.r/255.0) - k) / (1 - k)))
        m = int(100 * ((1 - (self.g/255.0) - k) / (1 - k)))
        y = int(100 * ((1 - (self.b/255.0) - k) / (1 - k)))
        return "cmyk(%s%%,%s%%,%s%%,%s%%)" % (c, m, y, k)
