from django.contrib import admin
from app.models import User, Page, Comment

# Register your models here.
admin.site.register(User)
admin.site.register(Page)
admin.site.register(Comment)