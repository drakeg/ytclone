from django.contrib import admin
from .models import Video, Channel, Category, Comment

# Register your models here.
admin.site.register(Video)
admin.site.register(Channel)
admin.site.register(Category)
admin.site.register(Comment)