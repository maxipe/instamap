from django.db import models

class Coordinate(models.Model):
    latitude = models.CharField(max_length=20)
    longitude = models.CharField(max_length=20)

class InstagramUser(models.Model):
    name = models.CharField(max_length=200)

class City(models.Model):
    name = models.CharField(max_length=200)
    center = models.ForeignKey(Coordinate)

class Photo(models.Model):
    date = models.DateTimeField('date of point')
    coordinate = models.ForeignKey(Coordinate)
    likes = models.IntegerField(default=0)
    coments = models.IntegerField(default=0)

    #Belongs to
    city = models.ForeignKey(City)
    author = models.ForeignKey(InstagramUser)

class InterestingArea(models.Model):
    coordinate = models.ForeignKey(Coordinate)

    #Belongs to
    city = models.ForeignKey(City)
