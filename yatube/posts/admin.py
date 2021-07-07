from django.contrib import admin

from .models import Post, Group, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['pk', 'text', 'pub_date', 'author', 'group']
    search_fields = ['text']
    list_filter = ['pub_date']
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'slug', 'description']
    search_fields = ['title']
    list_filter = ['slug']
    empty_value_display = '-пусто-'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['pk', 'post', 'author', 'text', 'created']
    search_fields = ['post', 'author', 'text']
    list_filter = ['created']
    empty_value_display = '-пусто-'
