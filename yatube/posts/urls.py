from django.urls import path

from . import views

app_name = 'posts'


urlpatterns = [
    path(
        'new/',
        views.new_post,
        name='new_post'
    ),
    path(
        '<str:username>/<int:post_id>/edit/',
        views.post_edit,
        name='edit_post'
    ),
    path(
        '<str:username>/<int:post_id>/',
        views.post_view,
        name='post'
    ),
    path(
        'group/<slug:slug>/',
        views.group_posts,
        name='group_posts'
    ),
    path(
        '<str:username>/',
        views.profile,
        name='profile'
    ),
    path(
        '',
        views.index,
        name='index'
    ),
    path(
        '<str:username>/<int:post_id>/comment',
        views.add_comment,
        name='add_comment'
    )
]
