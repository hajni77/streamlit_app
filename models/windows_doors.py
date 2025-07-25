class WindowsDoors:
    def __init__(self, name,wall, position, width,depth, height, hinge, way):
        self.name = name # name of the object
        self.wall = wall # type of the object, top, left, right, bottom
        self.position = position # position of the object, x, y(on the wall floor)
        self.width = width # width of the object
        self.depth = depth # depth of the object
        self.height = height # height of the object
        self.hinge = hinge # hinge of the object, left or right
        self.way = way # way of the object, inwards or outwards
    def get_door_walls(self):
        return self.wall

    def print_features(self):
        print("name: " + self.name)
        print("wall: " + self.wall)
        print("position: " + str(self.position))
        print("width: " + str(self.width))
        print("depth: " + str(self.depth))
        print("height: " + str(self.height))
        print("hinge: " + self.hinge)
        print("way: " + self.way)