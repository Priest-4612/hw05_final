from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовое сообщество',
            slug='test-slug',
            description='Тестовое описание сообщества'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст ' * 15,
            author=cls.author,
            group=cls.group,
        )
        cls.post_other = Post.objects.create(
            text='Тестовый текст другой автор' * 13,
            author=User.objects.create(username='other_test_user')
        )

    def setUp(self):
        cache.clear()

        self.guest_client = Client()
        self.user = PostURLTests.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        group = PostURLTests.group
        post = PostURLTests.post

        self.template_url_names = {
            '/': {
                'template': 'posts/index.html',
                'is_authorized_client': False,
                'redirect_page': '',
            },
            f'/group/{group.slug}/': {
                'template': 'group.html',
                'is_authorized_client': False,
                'redirect_page': '',
            },
            f'/{self.user.username}/': {
                'template': 'posts/profile.html',
                'is_authorized_client': False,
                'redirect_page': '',
            },
            f'/{self.user.username}/{post.pk}/': {
                'template': 'posts/post.html',
                'is_authorized_client': False,
                'redirect_page': '',
            },
            '/new/': {
                'template': 'posts/new_post.html',
                'is_authorized_client': True,
                'redirect_page': '/auth/login/?next=/new/',
            },
            f'/{self.user.username}/{post.pk}/edit/': {
                'template': 'posts/new_post.html',
                'is_authorized_client': True,
                'redirect_page': (
                    '/auth/login/?next=/'
                    f'{self.user.username}/{post.pk}/edit/'
                ),
            },
            '/follow/': {
                'template': 'posts/follow.html',
                'is_authorized_client': True,
                'redirect_page': '/auth/login/?next=/follow/',
            },
        }

    def test_urls_public_pages(self):
        """
        Тестирование общедоступных страниц
        """
        for address, params in self.template_url_names.items():
            if not params['is_authorized_client']:
                with self.subTest(address=address):
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code, 200)

    def test_urls_redirect_private_pages_anonymous(self):
        """
        Тесты редиректов для неавторизованного пользователя !!!.
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

    def test_urls_private_pages_autorized_user(self):
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

    def test_urls_redirect_update_other_post(self):
        '''
        Проверьте, правильно ли работает редирект со страницы
        /<username>/<post_id>/edit/для тех,
        у кого нет прав доступа к этой странице.
        '''
        post = PostURLTests.post_other
        response = self.authorized_client.get(
            f'/{post.author.username}/{post.pk}/edit/'
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/{post.author.username}/{post.pk}/')
