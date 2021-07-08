import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

from posts.models import Post, Group, User, Follow, Comment


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostViewTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.user = User.objects.create(username='test_user')
        self.other_user = User.objects.create(username='other_test_user')
        self.group = Group.objects.create(
            title='Тестовое сообщество',
            slug='test-slug',
            description='Тестовое описание сообщества'
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
            image=self.uploaded
        )
        self.other_post = Post.objects.create(
            text='Тестовый текст другой автор' * 13,
            author=self.other_user
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.other_client = Client()
        self.other_client.force_login(self.other_user)

        self.template_url_names = {
            reverse('posts:index'): {
                'template': 'posts/index.html',
                'is_authorized_client': False,
                'redirect_page': '',
            },
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}): {
                'template': 'group.html',
                'is_authorized_client': False,
                'redirect_page': '',
            },
            reverse('posts:profile', kwargs={
                'username': self.user.username
            }): {
                'template': 'posts/profile.html',
                'is_authorized_client': False,
                'redirect_page': '',
            },
            reverse('posts:post', kwargs={
                'username': self.user.username,
                'post_id': self.post.pk
            }): {
                'template': 'posts/post.html',
                'is_authorized_client': False,
                'redirect_page': '',
            },
            reverse('posts:new_post'): {
                'template': 'posts/new_post.html',
                'is_authorized_client': True,
                'redirect_page': '/auth/login/?next=/new/',
            },
            reverse('posts:post_edit', kwargs={
                'username': self.user.username,
                'post_id': self.post.pk
            }): {
                'template': 'posts/new_post.html',
                'is_authorized_client': True,
                'redirect_page': (
                    '/auth/login/?next=/'
                    f'{self.user.username}/{self.post.pk}/edit/'
                ),
            },
            reverse('posts:follow_index'): {
                'template': 'posts/follow.html',
                'is_authorized_client': True,
                'redirect_page': (
                    '/auth/login/?next=/follow/'
                ),
            }
        }

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page'][1]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.post.author.username)
        # self.assertEqual(post.group.slug, self.post.group.slug)
        # self.assertEqual(post.image, self.post.image)

    def test_group_page_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}
        ))
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(
            response.context['profile'].username,
            self.user.username
        )
        self.assertEqual(
            response.context['post_count'],
            self.user.posts.count()
        )
        self.assertEqual(response.context['post'].text, self.post.text)
        self.assertEqual(
            response.context['post'].author.username,
            self.post.author.username
        )
        self.assertEqual(
            response.context['post'].group.slug,
            self.post.group.slug
        )
        self.assertEqual(
            response.context['post'].image,
            self.post.image
        )

    def test_post_view_page_shows_correct_context(self):
        """Шаблон post_view сформирован с правильным контекстом."""
        profile = self.user
        response = self.authorized_client.get(
            reverse(
                'posts:post', kwargs={
                    'username': profile.username,
                    'post_id': self.post.pk
                }
            )
        )
        self.assertEqual(
            response.context['profile'].username,
            profile.username
        )
        self.assertEqual(
            response.context['post_count'],
            profile.posts.count()
        )
        self.assertEqual(response.context['post'].text, self.post.text)
        self.assertEqual(
            response.context['post'].author.username,
            self.post.author.username
        )
        self.assertEqual(
            response.context['post'].group.slug,
            self.post.group.slug
        )
        self.assertEqual(
            response.context['post'].image,
            self.post.image
        )

    def test_urls_exists_at_desired_location(self):
        """
        Тестирование общедоступных страниц
        """
        for address, params in self.template_url_names.items():
            if not params['is_authorized_client']:
                with self.subTest(address=address):
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code, 200)

    def test_urls_redirect_anonymous(self):
        """
        Тестирование редиректов для неавторизованного пользователя !!!.
        """
        for address, params in self.template_url_names.items():
            if params['is_authorized_client']:
                with self.subTest(address=address):
                    response = self.guest_client.get(
                        path=address,
                        follow=True
                    )
                    self.assertRedirects(
                        response,
                        params['redirect_page']
                    )

    def test_urls_exists_at_desired_location_autorized_user(self):
        """
        Тесты доступности страниц для авторизованного пользователя.
        """
        for address, params in self.template_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, params in self.template_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, params['template'])

    def test_edit_other_post_redirect(self):
        '''
        Проверьте, правильно ли работает редирект со страницы
        /<username>/<post_id>/edit/для тех,
        у кого нет прав доступа к этой странице.
        '''

        address_edit = reverse('posts:post_edit', kwargs={
            'username': self.other_user.username,
            'post_id': self.other_post.pk
        })
        address_post = reverse('posts:post', kwargs={
            'username': self.other_user.username,
            'post_id': self.other_post.pk
        })
        response = self.authorized_client.get(address_edit)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, address_post)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_paginator')
        cls.group = Group.objects.create(
            title='Тестовое сообщество',
            slug='test-slug-paginator',
            description='Тестовое описание сообщества для пагинатора'
        )
        for i in range(26):
            post = Post.objects.create(author=cls.user)
            post.text = f'Тестовый текст {1}'
            if i % 2 == 0:
                post.group = cls.group
            post.save()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page']), 10)

    def test_third_page_contains_six_records(self):
        response = self.guest_client.get(reverse('posts:index') + '?page=3')
        self.assertEqual(len(response.context['page']), 6)


class CacheTests(PostViewTests, TestCase):
    def test_cache_exists(self):
        '''
        Проверяем наличее кешируемого фрагмента index_page на странице index
        '''
        self.authorized_client.get(reverse('posts:index'))
        key = make_template_fragment_key('index_page')
        self.assertTrue(key in cache)

    def test_cached_index_page(self):
        '''
            Проверяем работу кеширования страницы index
        '''
        new_post = Post.objects.create(
            text='Тест кэша ' * 15,
            author=self.user,
            group=self.group,

        )
        response_before = self.authorized_client.get(reverse('posts:index'))
        page_before_del = response_before.context['page']
        paginator_before = page_before_del.paginator
        self.assertEqual(paginator_before.num_pages, 1)
        self.assertEqual(paginator_before.count, 3)
        self.assertEqual(page_before_del[0].text, new_post.text)
        self.assertEqual(page_before_del[0].author, new_post.author)
        new_post.delete()
        response_after = self.authorized_client.get(reverse('posts:index'))
        self.assertIsNone(response_after.context)
        cache.clear()
        response_after = self.authorized_client.get(reverse('posts:index'))
        page_after_del = response_after.context['page']
        paginator_after = page_after_del.paginator
        self.assertEqual(paginator_after.num_pages, 1)
        self.assertNotEqual(paginator_after.count, 3)


class FollowViewsTests(PostViewTests, TestCase):
    '''
    Авторизованный пользователь может подписываться на других пользователей
    и удалять их из подписок.
    '''
    def test_profile_follow_redirect_anonymous(self):
        address = reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}
        )
        with self.subTest(address=address):
            response = self.guest_client.get(
                path=address,
                follow=True
            )
            self.assertRedirects(
                response,
                (
                    '/auth/login/?next=/'
                    f'{self.user.username}/follow/'
                )
            )

    def test_profile_follow_redirect_anonymous(self):
        address = reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user.username}
        )
        with self.subTest(address=address):
            response = self.guest_client.get(
                path=address,
                follow=True
            )
            self.assertRedirects(
                response,
                (
                    '/auth/login/?next=/'
                    f'{self.user.username}/unfollow/'
                )
            )

    def test_profile_follow_autorized_user(self):
        address = reverse(
            'posts:profile_follow',
            kwargs={'username': self.other_user.username}
        )
        follow_count_before = Follow.objects.all().count()
        self.assertEqual(follow_count_before, 0)
        self.authorized_client.get(address)
        follow_count_after = Follow.objects.all().count()
        self.assertEqual(follow_count_after, 1)

    def test_profile_follow_autorized_user(self):
        address = reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.other_user.username}
        )
        Follow.objects.create(
            user=self.user,
            author=self.other_user
        )
        follow_count_before = Follow.objects.all().count()
        self.assertEqual(follow_count_before, 1)
        self.authorized_client.get(address)
        follow_count_after = Follow.objects.all().count()
        self.assertEqual(follow_count_after, 0)

    def test_follow_correct_show(self):
        '''
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан на него.
        '''
        Follow.objects.create(
            user=self.user,
            author=self.other_user
        )
        Follow.objects.create(
            user=self.other_user,
            author=self.user
        )
        new_post = Post.objects.create(
            text='text text text',
            author=self.other_user
        )
        address = reverse('posts:follow_index')
        response_following = self.authorized_client.get(address)
        post_is_exists = new_post in response_following.context['page']
        self.assertTrue(post_is_exists)
        response_other = self.other_client.get(address)
        post_is_not_exists = new_post not in response_other.context['page']
        self.assertTrue(post_is_not_exists)


class CommentViewsTests(PostViewTests, TestCase):
    '''
    Только авторизированный пользователь может комментировать посты.
    '''

    def test_add_comment_redirect_anonymous(self):
        address = reverse(
            'posts:add_comment',
            kwargs={
                'username': self.user.username,
                'post_id': self.post.pk
            }
        )
        with self.subTest(address=address):
            response = self.guest_client.get(
                path=address,
                follow=True
            )
            self.assertRedirects(
                response,
                (
                    '/auth/login/?next=/'
                    f'{self.user.username}/{self.post.pk}/comment'
                )
            )

    def test_add_comment(self):
        address = reverse(
            'posts:add_comment',
            kwargs={
                'username': self.user.username,
                'post_id': self.post.pk
            }
        )
        form_data = {
            'text': 'comment comment commetn'
        }
        self.authorized_client.post(
            address,
            data=form_data,
            follow=True
        )
        comment_is_created = Comment.objects.filter(
            text=form_data['text']
        ).exists()
        self.assertTrue(comment_is_created)
