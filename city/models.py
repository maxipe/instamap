from django.db import models

class Coordinate(models.Model):
    latitude = models.CharField(max_length=20)
    longitude = models.CharField(max_length=20)

class InstagramUser(models.Model):
    name = models.CharField(max_length=200)

class Photo(models.Model):
    date = models.DateTimeField('date of point')
    coordinate = models.ForeignKey(Coordinate)
    author = models.ForeignKey(InstagramUser)
    likes = models.IntegerField(default=0)
    coments = models.IntegerField(default=0)

class City(models.Model):
    name = models.CharField(max_length=200)
    center = models.ForeignKey(Coordinate)

    #FIXME: These should be lists.
    photos = models.ForeignKey(Photo)
    interestingAreas = models.ForeignKey(Point)
