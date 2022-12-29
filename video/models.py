from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='categories/thumbnails')

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='videos/thumbnails')
    video_file = models.FileField(upload_to='videos/files')
    views = models.PositiveIntegerField(default=0)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    likes = models.ManyToManyField(User, related_name='likes', blank=True)
    dislikes = models.ManyToManyField(User, related_name='dislikes', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}: {1} - {2}".format(self.author, self.pub_date, self.video)

class Channel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='channels/thumbnails')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    subscribers = models.ManyToManyField(User, related_name='subscriptions', blank=True)

    def __str__(self):
        return self.name