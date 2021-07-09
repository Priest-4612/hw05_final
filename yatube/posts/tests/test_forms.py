import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.author = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовое сообщество',
            slug='test-slug',
            description='Тестовое описание сообщества'
        )
        cls.post_edit = Post.objects.create(
            text='Редактируемый текст',
            author=cls.author
        )
        Post.objects.create(
            text='Тестовый текст ' * 15,
            author=cls.author,
            group=cls.group,
        )
        Post.objects.create(
            text='Тестовый текст ' * 5,
            author=cls.author
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.group = PostCreateFormTests.group
        self.uploaded = PostCreateFormTests.uploaded
        self.count_post = Post.objects.count()
        self.count_group_count = self.group.posts.count()
        self.user = PostCreateFormTests.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_new_post(self):
        """Проверяем создан новый пост."""
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.pk,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.latest("pk")
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.pk, form_data['group'])
        self.assertEqual(new_post.image, f"posts/{form_data['image']}")
        self.assertEqual(Post.objects.count(), self.count_post + 1)
        self.assertEqual(self.group.posts.count(), self.count_group_count + 1)

    def test_form_page_shows_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        response = self.authorized_client.get(reverse('posts:new_post'))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_update_post(self):
        """Проверяем обновление поста поста."""
        post_edit = PostCreateFormTests.post_edit
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.pk
        }
        address_post = reverse(
            'posts:post_edit',
            kwargs={
                'username': post_edit.author.username,
                'post_id': post_edit.pk
            }
        )
        response = self.authorized_client.post(
            address_post,
            data=form_data,
            follow=True
        )

        post_edit.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post_edit.text, form_data['text'])
        self.assertEqual(post_edit.group.pk, form_data['group'])
