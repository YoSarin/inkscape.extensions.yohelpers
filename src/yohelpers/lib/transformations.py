from abc import ABCMeta, abstractmethod
import re

class Transformation():
    __metaclass__ = ABCMeta

    @abstractmethod
    def Apply(self, x, y):
        pass

    @staticmethod
    def Parse(element):
        transformations = []
        if hasattr(element, "attrib") and "transform" in element.attrib:
            matches = re.findall("([a-z]+)\(([^)]+)\)", element.attrib["transform"])
            for match in matches:
                type = match[0]
                params = [float(i) for i in re.findall(r"-?[0-9.]+", match[1])]
                if type == "translate":
                    transformations.append(TranslateTransformation(*params))
                elif type == "matrix":
                    transformations.append(MatrixTransformation(*params))
        return transformations

class TranslateTransformation(Transformation):
    moveX = 0
    moveY = 0

    def __init__(self, moveX, moveY = 0):
        self.moveX = moveX
        self.moveY = moveY

    def Apply(self, x, y):
        return (x + self.moveX, y + self.moveY)

class MatrixTransformation(Transformation):
    a = 0
    b = 0
    c = 0
    d = 0
    e = 0
    f = 0

    def __init__(self, a, b, c, d, e, f):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    def Apply(self, x, y):
        newX = self.a * x + self.c * y + self.e
        newY = self.b * x + self.d * y + self.f
        return (newX, newY)
