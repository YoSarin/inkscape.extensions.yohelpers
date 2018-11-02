from box import Box


class Element:
    path = None
    transformations = []

    def __init__(self, path, transformations):
        self.path = path
        self.transformations = transformations

    def changeStyle(self, style):
        originalStyle = {}
        if "style" in self.path.attrib:
            originalStyle = {i.split(":")[0]: i.split(":", 1)[1] for i in self.path.attrib["style"].split(";")}

        for name in style:
            originalStyle[name] = style[name]

        self.path.set("style", ";".join(["%s:%s" % (k, originalStyle[k]) for k in originalStyle]))

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
