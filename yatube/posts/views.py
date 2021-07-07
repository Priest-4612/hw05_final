from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from .forms import PostForm, CommentForm
from django.views.decorators.cache import cache_page

from .models import Post, Group, User


def make_pagination(request, object_list, per_page):
    paginator = Paginator(object_list, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def page_not_found(request, exception):
    return render(
        request,
        'errors/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'errors/500.html', status=500)


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    page = make_pagination(request, post_list, 10)
    context = {'page': page}

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page = make_pagination(request, posts, 10)
    context = {'group': group, 'page': page}

    return render(request, 'group.html', context)


def profile(request, username):
    profile = get_object_or_404(
        User.objects.annotate(posts_count=Count('posts')),
        username=username
    )
    posts = profile.posts.all()
    post_count = profile.posts_count
    page = make_pagination(request, posts, 10)

    context = {'profile': profile, 'page': page, 'post_count': post_count}
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    profile = get_object_or_404(
        User.objects.annotate(posts_count=Count('posts')),
        username=username
    )
    post = get_object_or_404(profile.posts, pk=post_id)
    post_count = profile.posts_count
    form = CommentForm()
    comments = post.comments.all()

    context = {
        'profile': profile,
        'post': post,
        'post_count': post_count,
        'comments': comments,
        'form': form
    }

    return render(request, 'posts/post.html', context)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        path = reverse(
            'posts:post',
            kwargs={'username': username, 'post_id': post_id}
        )
        return redirect(path)

    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'mixins/comments.html', context)


@login_required
def new_post(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:index')

    context = {
        'form': form,
        'title': 'Добавить',
        'submit': 'Добавить'
    }

    return render(request, 'posts/new_post.html', context)


@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    path = reverse(
        'posts:post',
        kwargs={'username': username, 'post_id': post_id}
    )

    if request.user.pk != profile.pk:
        return redirect(path)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect(path)

    context = {
        'form': form,
        'title': 'Редактировать',
        'submit': 'Сохранить'
    }

    return render(request, 'posts/new_post.html', context)
