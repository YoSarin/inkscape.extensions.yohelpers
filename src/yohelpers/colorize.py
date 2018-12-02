#! /usr/bin/python
# -*- coding: utf-8 -*-
import random
import argparse
import math
import re
import os
import traceback
from xml.dom import minidom
import parser

from lib.color import Color
from lib.box import Box
from lib.element import Element
from lib.transformations import Transformation
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

def fill(root, paths, color_space, grayscale, randomness, colors, tones):
    box = boundaries(root, paths)
    # print box.width(), box.height()
    for element in paths:
        try:
            localBox = boundaries(root, [element])
            color = determineColor(box, localBox, grayscale, randomness, colors, tones)
            element.changeStyle({
                "fill" : color.rgb() if color_space == "rgb" else color.cmyk()
            })
        except:
            pass

def stroke(root, paths, color_space, width, color):
    for element in paths:
        try:
            element.changeStyle({
                "stroke" : color.rgb() if color_space == "rgb" else color.cmyk(),
                "stroke-width" : "%smm" % width
            })
        except:
            pass

def opacity(root, paths, remove, start, end, formula):
    box = centerBoundaries(root, paths)
    # print box.width(), box.height()
    for element in paths:
        try:
            if remove:
                element.removeStyle(["fill-opacity", "stroke-opacity"])
                continue

            localBox = boundaries(root, [element])
            validate(formula)
            x = box.relativeX(localBox.centerX())/100
            y = box.relativeY(localBox.centerY())/100
            evalRes = evalFormula(formula, x, y)
            opacity = min(start, end) + (abs(start - end) * evalRes)
            # debug("%s + (abs(%s - %s) * %s) = %.2f" % (min(start, end), start, end, formula, opacity))
            # debug("%s + (abs(%s - %s) * %s) = %.2f" % (min(start, end), start, end, evalRes, opacity))
            element.changeStyle({
                "fill-opacity": "%.2f" % opacity
            })
        except Exception as e:
            debug(e)
            debug(traceback.format_exc())
            pass

def validate(formula):
    # allowed functions
    cleaned = re.sub(r"(?:^|(?<=\W))(abs|min|max|sin|cos|log10|log)(?:(?=\s*\())", "", formula, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?:^|(?<=\W))(x|y)(?:(?=\W)|$)", "", cleaned, flags=re.IGNORECASE)
    if re.search("[a-z]", cleaned, flags=re.IGNORECASE):
        raise Exception("Possibly dangerous formula: '" + cleaned + "' (" + formula + ")")

def evalFormula(formula, x, y):
    from math import sin, cos, log, log10
    return eval(formula)

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
        baseR = base.r
        baseG = base.g
        baseB = base.b

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


def centerBoundaries(root, elements):
    b = Box()
    for element in elements:
        eb = element.Boundaries()
        if b.minX == None or b.minX > eb.centerX():
            b.minX = eb.centerX()
        if b.minY == None or b.minY > eb.centerY():
            b.minY = eb.centerY()
        if b.maxX == None or b.maxX < eb.centerX():
            b.maxX = eb.centerX()
        if b.maxY == None or b.maxY < eb.centerY():
            b.maxY = eb.centerY()
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
    elements = [el for el in elements if isSelected or el.path.get("id") in selectedElements]
    # filter to not include hidden/locked ones
    elements = [el for el in elements if not isLockedOrHidden(el.path)]
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
        self.OptionParser.add_option("--change_fill", default=False, **boolParams)
        self.OptionParser.add_option("--change_lines", default=False, **boolParams)
        self.OptionParser.add_option("--change_opacity", default=False, **boolParams)

        self.OptionParser.add_option("--color_space", default="rgb")
        self.OptionParser.add_option("--grayscale", default=False, **boolParams)
        self.OptionParser.add_option("--tones", default=False, **boolParams)
        self.OptionParser.add_option("--randomness", type="int", default=15, help=u"Procentní vyjádření jak moc může barva ustřelit do jakéhokoli směru (0 => plynulé přechody; 100 => kompletně random)")
        self.OptionParser.add_option("--colors", type="str", help=u"list barev (formát rrggbb (hexa)) jejichž variace mají být použité")

        self.OptionParser.add_option("--lines_width", type="float", default=0.0)
        self.OptionParser.add_option("--lines_color", default="#ffffff")

        self.OptionParser.add_option("--remove_opacity", default=False, **boolParams)
        self.OptionParser.add_option("--opacity_start", type="float", default=1.0)
        self.OptionParser.add_option("--opacity_end", type="float", default=0.0)
        self.OptionParser.add_option("--opacity_formula", default="1/x")

        self.OptionParser.add_option("--active-tab", help="no use in CLI")


    def effect(self):
        tree = None
        if self.options.input_filename:
            tree = etree.parse(open(self.options.input_filename))
        else:
            tree = self.document

        paths = findElements(tree, "path", self.selected)
        polygons = findElements(tree, "polygon", self.selected)
        colors = None if not self.options.colors else [Color.FromRGB(c) for c in re.findall("[a-z0-9]{6}", self.options.colors, re.IGNORECASE)]

        if self.options.change_fill:
            fill(tree, paths + polygons, self.options.color_space, self.options.grayscale, self.options.randomness, colors, self.options.tones)
        if self.options.change_lines:
            stroke(tree, paths + polygons, self.options.color_space, self.options.lines_width, Color.FromRGB(self.options.lines_color))
        if self.options.change_opacity:
            opacity(tree, paths + polygons, self.options.remove_opacity, float(self.options.opacity_start), float(self.options.opacity_end), self.options.opacity_formula)

        if self.options.input_filename:
            etree.register_namespace('namespace',"http://www.w3.org/2000/svg")
            xml = etree.tostring(tree.getroot())
            xml =  minidom.parseString(xml).toprettyxml(indent="  ")
            target_file = output_file(self.options.input_filename, self.options.color_space)
            if self.options.overwrite:
                target_file = self.options.input_filename
            with open(target_file, 'w') as file:
                file.write(re.sub("(\s*\n)+", "\n", xml, re.MULTILINE))
'''
def debug(data):
    pass
'''
if __name__ == "__main__":
    ext = ColorizeExtension()
    ext.affect()
