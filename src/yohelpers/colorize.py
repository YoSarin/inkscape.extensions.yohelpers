#! /usr/bin/python
# -*- coding: utf-8 -*-
import random
import argparse
import math
import re
import os
import traceback
from xml.dom import minidom
from abc import ABCMeta, abstractmethod
# __version__ = "0.1"

boolParams = {"type": "inkbool"}

try:
    from inkex import localize, Effect, debug, etree
    localize()
except:
    # magic needed to made it work from cli
    from optparse import OptionParser
    from lxml import etree

    boolParams = {"action": "store_true"}

    def debug(data):
        print data

    class Effect:

        OptionParser = OptionParser()
        options = None

        def __init__(self):
            pass

        def affect(self):
            self.options = self.OptionParser.parse_args()[0]
            self.effect();

def colorize(root, paths, color_space, grayscale, randomness, colors, lines_width, tones):
    box = boundaries(root, paths)
    # print box.width(), box.height()
    for element in paths:
        path = element.path
        style = []
        if "style" in path.attrib:
            style = path.attrib["style"].split(";")
        newStyle = []
        localBox = boundaries(root, [element])
        color = determineColor(box, localBox, grayscale, randomness, colors, tones)
        for value in style:
            data = value.split(":")
            if data[0] in ["fill", "stroke", "stroke-width"]:
                continue
            newStyle.append(":".join(data))

        newStyle.append("fill:%s" % (color.rgb() if color_space == "rgb" else color.cmyk()))
        newStyle.append("stroke:%s" % ("#ffffff" if color_space == "rgb" else "cmyk(0%,0%,0%,0%)"))
        newStyle.append("stroke-width:%smm" % (lines_width))

        debug(root)
        debug(path.get("style"))
        path.set("style", ";".join(newStyle))
        debug(path.get("style"))

def determineColor(outterBox, innerBox, grayscale, randomness, colors, tones):
    color = Color()

    randomness = int((randomness/100.0)*255);

    # color.r = max(0, min(255, int(outterBox.relativeX(innerBox.minX, 255)) + random.randint(-spread,spread)))
    # color.g = color.r if grayscale else max(0, min(255, int(outterBox.relativeY(innerBox.minY, 255)) + random.randint(-spread,spread)))
    # color.b = color.r if grayscale else  max(0, min(255, (color.r+color.g)/2 + random.randint(-spread,spread)))
    baseB = int((((outterBox.relativeX(innerBox.minX) - 50)/50)**2)*255)
    baseG = int((((outterBox.relativeY(innerBox.minY) - 50)/50)**2)*255)
    baseR = int((baseB+baseG)/2)

    if colors is not None:
        # sem by se hodilo něco komplexnějšího, ať je nějaký pattern...
        base = colors[random.randint(0, len(colors) - 1)]
        baseR = int(base[0:2], 16)
        baseG = int(base[2:4], 16)
        baseB = int(base[4:6], 16)

    if tones:
        negative = min(randomness, baseR if baseR else 255, baseG if baseG else 255, baseB if baseB else 255)
        positive = min(randomness, (255 - baseR) if baseR < 255 else 255, (255 - baseG) if baseG < 255 else 255, (255 - baseB) if baseB < 255 else 255)
        diff = random.randint(-negative, positive)
        color.r = max(0, min(255, baseR + diff))
        color.g = color.r if grayscale else max(0, min(255, baseG + diff))
        color.b = color.r if grayscale else max(0, min(255, baseB + diff))
    else:
        color.b = random.randint(min(255, max(0, baseB - randomness)), min(255, max(0, baseB + randomness)))
        color.g = color.b if grayscale else random.randint(min(255, max(0, baseG - randomness)), min(255, max(0, baseG + randomness)))
        color.r = color.b if grayscale else random.randint(min(255, max(0, baseR - randomness)), min(255, max(0, baseR + randomness)))

    return color

def boundaries(root, elements):
    b = Box()
    for element in elements:
        eb = element.Boundaries()
        if b.minX == None or b.minX > eb.minX:
            b.minX = eb.minX
        if b.minY == None or b.minY > eb.minY:
            b.minY = eb.minY
        if b.maxX == None or b.maxX < eb.maxX:
            b.maxX = eb.maxX
        if b.maxY == None or b.maxY < eb.maxY:
            b.maxY = eb.maxY
        # print eb.coords(), b.coords()
    return b

def output_file(input_filename, color_space):
    parts = input_filename.split(".")
    parts.insert(-1, "colorized")
    parts.insert(-1, color_space)
    return ".".join(parts)

def findElements(root, name, selectedElements, isSelected = False, transformations = []):

    transformations += Transformation.Parse(root)
    if len(selectedElements) == 0 or (hasattr(root, "get") and root.get("id") in selectedElements):
        isSelected = True

    if isLockedOrHidden(root):
        return []

    groups = root.findall("ns:g", namespaces = {"ns":"http://www.w3.org/2000/svg"})
    elements = [Element(el, transformations[:]) for el in root.findall("ns:" + name, namespaces = {"ns":"http://www.w3.org/2000/svg"})]
    # filter to selected ones
    debug(elements)
    elements = [el for el in elements if isSelected or el.path.get("id") in selectedElements]
    # filter to not hidden/locked tones
    elements = [el for el in elements if not isLockedOrHidden(el.path)]
    debug(elements)
    for group in groups:
        elements = elements + findElements(group, name, selectedElements, isSelected, transformations[:])
    return elements

def isLockedOrHidden(element):
    if not hasattr(element, "get"):
        return False
    if element.get("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}insensitive") == "true":
        # inkscape locked
        return True
    style = element.get("style")
    if style and "display:hidden" in style:
        # inkscape locked
        return True
    return False

class Color:
    r = 0
    g = 0
    b = 0

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

class Element:
    path = None
    transformations = []

    def __init__(self, path, transformations):
        self.path = path
        self.transformations = transformations

    def Transform(self, x, y):
        if len(self.transformations) > 0:
            # print "==== %s ===" % self.path.attrib["id"]
            # print "%s %s => (%s) =>" % (x, y, ", ".join([t.__class__.__name__ for t in self.transformations])),
            pass
        for transform in reversed(self.transformations):
            (x, y) = transform.Apply(x, y)

        # print "%s %s" % (x, y)

        return (x, y)

    def Boundaries(self):
        b = Box()
        path = self.path

        currX = currY = None
        additive = False
        currentSkip = skip = -1
        coords = []
        if "d" in path.attrib:
            coords = path.attrib["d"].split(" ")
            if coords[0] == "M":
                additive = False
                coords = coords[1:]
        elif "points" in path.attrib:
            additive = False
            coords = path.attrib["points"].split(" ")

        for command in coords:
            try:
                xy = command.split(",")
                x = float(xy[0])
                y = float(xy[1])

                if currentSkip < 0 and skip > 0:
                    currentSkip = skip
                if currentSkip > 0:
                    currentSkip -= 1
                    # print "skipping", command, currentSkip, skip
                    continue
                if currentSkip == 0:
                    # print "processing", command
                    currentSkip -= 1

                if not additive or currX is None:
                    currX = x
                    currY = y
                else:
                    currX += x
                    currY += y
                (transX, transY) = self.Transform(currX, currY)

                if b.minX == None or b.minX > transX:
                    b.minX = transX
                if b.minY == None or b.minY > transY:
                    b.minY = transY
                if b.maxX == None or b.maxX < transX:
                    b.maxX = transX
                if b.maxY == None or b.maxY < transY:
                    b.maxY = transY
            except Exception as e:
                # traceback.print_exc()
                skip = -1
                if command == "z" or command == "Z":
                    continue
                if command.upper() == command:
                    additive = False
                    currX = currY = None
                else:
                    additive = True
                if command == "c" or command == "C":
                    skip = 2
        return b


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

class ColorizeExtension(Effect):
    def __init__(self):
        Effect.__init__(self)

        # Two ways to get debug info:
        # OR just use inkex.debug(string) instead...
        try:
            self.tty = open("/dev/tty", 'w')
        except:
            self.tty = open(os.devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.
            # print >>self.tty, "gears-dev " + __version__

        self.OptionParser.add_option("--input_filename")
        self.OptionParser.add_option("--overwrite", default=False, **boolParams)
        self.OptionParser.add_option("--color_space", default="rgb")
        self.OptionParser.add_option("--active-tab", help="no use in CLI")
        self.OptionParser.add_option("--grayscale", default=False, **boolParams)
        self.OptionParser.add_option("--tones", default=False, **boolParams)
        self.OptionParser.add_option("--lines_width", type="float", default=0.0)
        self.OptionParser.add_option("--randomness", type="int", default=15, help=u"Procentní vyjádření jak moc může barva ustřelit do jakéhokoli směru (0 => plynulé přechody; 100 => kompletně random)")
        self.OptionParser.add_option("--colors", type="str", help=u"list barev (formát rrggbb (hexa)) jejichž variace mají být použité")

    def effect(self):
        tree = None
        if self.options.input_filename:
            tree = etree.parse(open(self.options.input_filename))
        else:
            tree = self.document

        debug(self.selected)

        paths = findElements(tree, "path", self.selected)
        polygons = findElements(tree, "polygon", self.selected)
        colors = None if not self.options.colors else re.findall("[a-z0-9]{6}", self.options.colors, re.IGNORECASE)

        colorize(tree, paths + polygons, self.options.color_space, self.options.grayscale, self.options.randomness, colors, self.options.lines_width, self.options.tones)

        if self.options.input_filename:
            etree.register_namespace('namespace',"http://www.w3.org/2000/svg")
            xml = etree.tostring(tree.getroot())
            xml =  minidom.parseString(xml).toprettyxml(indent="  ")
            target_file = output_file(self.options.input_filename, self.options.color_space)
            if self.options.overwrite:
                target_file = self.options.input_filename
            with open(target_file, 'w') as file:
                file.write(re.sub("(\s*\n)+", "\n", xml, re.MULTILINE))

def debug(data):
    pass

if __name__ == "__main__":
    ext = ColorizeExtension()
    ext.affect()
