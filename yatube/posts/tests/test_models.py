from django.test import TestCase

from posts.models import Post, User, Group


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            username='test_user'
        )

        cls.group = Group.objects.create(
            title='Котики правят миром',
            slug='Cat',
            description='Тестовое описание группы'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст ' * 15,
            author=cls.user,
            group=cls.group,
        )

    def test_object_name_is_text_fild(self):
        """
        В поле __str__  объекта post записано значение поля post.text
        длинной 15 символов
        """
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Котики правят миром',
            slug='Cat',
            description='Тестовое описание группы'
        )

    def test_object_name_is_title_fild(self):
        """
        В поле __str__  объекта group записано значение поля group.title
        """
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
