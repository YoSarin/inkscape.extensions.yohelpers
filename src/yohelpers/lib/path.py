class Path:
    path = ""
    points = []
    transformations = []

    def __init__(self, path, transformations):
        self.path = path
        self.transformations = transformations
        self._calculatePoints()

    def _calculatePoints(self):
        self.points = []
        coords = self.path.split("")
        state = None
        while(len(coords) > 0):
            token = coords.pop(0)
            if token.isalpha():
                state = State(token)
                continue
            else:
                if state and state.toSkip:
                    state.toSkip -= 1
                    continue

                xy = token.split(",")
                if state.isHorizontal():
                    x = xy[0]
                    y = None
                elif state.isVertical():
                    x = xy[0]
                    y = None

class State:
    command = ""
    isAbsolute = True
    toSkip = 0

    def __init__(self, token):
        self.command = token
        self.isAbsolute = (token == token.upper())
        if (token.upper() == "C"):
            toSkip = 2

    def isHorizontal(self):
        return command.upper() == "H"

    def isVertical(self):
        return command.upper() == "V"
