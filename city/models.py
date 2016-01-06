from django.db import models
import geopy.distance

class Coordinate(models.Model):
    latitude = models.CharField(max_length=20)
    longitude = models.CharField(max_length=20)

    def distance(self, other):
        gc = geopy.distance.great_circle()
        myPoint = geopy.distance.Point(self.latitude, self.longitude)
        otherPoint = geopy.distance.Point(other.latitude, other.longitude)

        return gc.measure(myPoint, otherPoint)

    def __str__(self):
        return "("+str(self.latitude)+" , "+str(self.longitude)+")"

class InstagramUser(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=200)
    center = models.ForeignKey(Coordinate)

    def __str__(self):
        return self.name

class Block(models.Model):
    lowerLeft = models.ForeignKey(Coordinate, related_name='LL')
    upperRight = models.ForeignKey(Coordinate, related_name='UR')

    def contains(self, c):
        '''C is Coordinate. '''
        return \
            c.latitude > lowerLeft.latitude and \
            c.latitude < upperRight.latitude and \
            c.longitude > lowerLeft.longitude and \
            c.longitude < upperRight.longitude

"""
class Block(object):

    def contains(self, c):
        '''C is Point. '''
        return \
            c.x >= lowerLeft.x and \
            c.x < upperRight.x and \
            c.y >= lowerLeft.y and \
            c.y < upperRight.y

    def divideInFour(self):
        leftX = lowerLeft.x
        rightX = upperLeft.x
        middleX = (rightX + leftX) / 2.0

        bottomY = lowerLeft.y
        topY = upperRight.y
        middleY = (topY + bottomY) / 2.0

        middlePoint = Point(middleX, middleY)

        topLeft = Block( Point(leftX,middleY), Point(middleX,topY) )
        topRight = Block( middlePoint, self.upperRight )
        bottomLeft = Block( self.lowerLeft, middlePoint )
        bottomRight = Block( Point(middleX,bottomY), Point(rightX,middleY) )

        return topLeft, topRight, bottomLeft, bottomRight

class QuadTree(object):
    NODE_CAPACITY = 10

    @classmethod
    #http://stackoverflow.com/questions/843580/writing-a-init-function-to-be-used-in-django-model
    def create(self, block):

        self.block = block
        self.points = []

        self.northWest = None
        self.northEast = None
        self.southWest = None
        self.southEast = None

    def contains(self, point):
        return self.block.contains(point)

    def subdivide(self):
        self.northWest, self.northEast, self.southWest, self.southEast = self.block.divideInFour()

    def insert(self, point):

        if len(points) < NODE_CAPACITY:
            self.points.append(point)
            return True

        if not self.northWest:
            self.subdivide()

        if self.insert(self.northWest) return True
        if self.insert(self.northEast) return True
        if self.insert(self.southWest) return True
        if self.insert(self.southEast) return True

        raise Exception("QuadTree didn't find a subtree...")
"""

class Photo(models.Model):
    #date = models.DateTimeField('date of point')
    coordinate = models.ForeignKey(Coordinate)
    #likes = models.IntegerField(default=0)
    #coments = models.IntegerField(default=0)
    link = models.CharField(max_length=200)

    #Belongs to
    #city = models.ForeignKey(City)
    #author = models.ForeignKey(InstagramUser)

    def __str__(self):
        #return "In "+str(self.city)+" by "+str(self.author)+" at "+str(self.date)+"."
        return "Photo at "+str(self.coordinate)

    def distance(self, other):
        return self.coordinate.distance(other.coordinate)

class InterestingArea(models.Model):
    coordinate = models.ForeignKey(Coordinate)

    #Belongs to
    city = models.ForeignKey(City)

    def __str__(self):
        return str(self.coordinate)+" at "+self.city+"."
