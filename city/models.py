from django.db import models

class Coordinate(models.Model):
    latitude = models.CharField(max_length=20)
    longitude = models.CharField(max_length=20)

    def __str__(self):
        return "("+self.latitude+" , "+self.longitude+")"

class InstagramUser(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=200)
    center = models.ForeignKey(Coordinate)

    def __str__(self):
        return self.name

class Photo(models.Model):
    date = models.DateTimeField('date of point')
    coordinate = models.ForeignKey(Coordinate)
    likes = models.IntegerField(default=0)
    coments = models.IntegerField(default=0)
    link = models.CharField(max_length=200)

    #Belongs to
    city = models.ForeignKey(City)
    author = models.ForeignKey(InstagramUser)

    def __str__(self):
        return "In "+str(self.city)+" by "+str(self.author)+" at "+str(self.date)+"."

class InterestingArea(models.Model):
    coordinate = models.ForeignKey(Coordinate)

    #Belongs to
    city = models.ForeignKey(City)

    def __str__(self):
        return str(self.coordinate)+" at "+self.city+"."
