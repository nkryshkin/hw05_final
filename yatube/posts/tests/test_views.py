import shutil
import tempfile
from itertools import islice, chain

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Follow
from posts.forms import PostForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user_2 = User.objects.create_user(username='AnotherAuthor')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Описание тестовой группы'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group-slug-2',
            description='Описание тестовой группы'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        group_slug = self.group.slug
        user_name = self.user.username
        post_id = self.post.id
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': group_slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': user_name}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': post_id}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': post_id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text = self.post.text
        post_group = self.post.group.title
        post_author = self.post.author.username
        fields = {
            first_object.text: post_text,
            first_object.group.title: post_group,
            first_object.author.username: post_author,
            first_object.image: 'posts/small.gif'
        }
        for field_recived, field_expected in fields.items():
            with self.subTest(field_recived=field_recived):
                self.assertEqual(field_expected, field_recived)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        group_slug = self.group.slug
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': group_slug})
        )
        first_object = response.context['page_obj'][0]
        group_recived = response.context['group']
        post_text = self.post.text
        post_group = self.post.group.title
        post_author = self.post.author.username
        group_title = self.group.title
        group_description = self.group.description
        fields = {
            first_object.text: post_text,
            first_object.group.title: post_group,
            first_object.author.username: post_author,
            first_object.image: 'posts/small.gif',
            group_recived.title: group_title,
            group_recived.slug: group_slug,
            group_recived.description: group_description,
        }
        for field_recived, field_expected in fields.items():
            with self.subTest(field_recived=field_recived):
                self.assertEqual(field_expected, field_recived)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        user_name = self.user.username
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': user_name})
        )
        first_object = response.context['page_obj'][0]
        author_recived = response.context['author']
        post_text = self.post.text
        post_group = self.post.group.title
        post_author = self.post.author.username
        fields = {
            first_object.text: post_text,
            first_object.group.title: post_group,
            first_object.author.username: post_author,
            first_object.image: 'posts/small.gif',
            author_recived.username: user_name,
        }
        for field_recived, field_expected in fields.items():
            with self.subTest(field_recived=field_recived):
                self.assertEqual(field_expected, field_recived)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        post_id = self.post.id
        post_text = self.post.text
        post_group = self.post.group.title
        post_author = self.post.author.username
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )
        object = response.context['post']
        count_recived = response.context['count']
        count_expected = self.user.posts.count()
        fields = {
            object.text: post_text,
            object.group.title: post_group,
            object.author.username: post_author,
            object.image: 'posts/small.gif',
            count_recived: count_expected
        }
        for field_recived, field_expected in fields.items():
            with self.subTest(field_recived=field_recived):
                self.assertEqual(field_expected, field_recived)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        post_id = self.post.id
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_id})
        )
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        object = response.context['post']
        fields = {
            object.text: 'Тестовый текст',
            object.group.title: 'Тестовая группа',
            object.author.username: 'HasNoName',
        }
        for field_recived, field_expected in fields.items():
            with self.subTest(field_recived=field_recived):
                self.assertEqual(field_expected, field_recived)

    def test_created_post_appears_in_correct_pages(self):
        """Созданный пост появляется на главной странице, на странице
        соответствующей группы, в профиле автора и отсутствует
        на странице другой группы и в профиле другого пользователя."""
        group_slug = self.group.slug
        user_name = self.user.username
        reverses = {
            1: reverse('posts:index'),
            2: reverse('posts:group_list', kwargs={'slug': group_slug}),
            3: reverse('posts:profile', kwargs={'username': user_name}),
        }
        for number, reverse_ in reverses.items():
            with self.subTest(number=number):
                response = self.authorized_client.get(reverse_)
                self.assertIn(self.post, response.context['page_obj'])
        group_slug_2 = self.group_2.slug
        user_name_2 = self.user_2.username
        reverses = {
            1: reverse('posts:group_list', kwargs={'slug': group_slug_2}),
            2: reverse('posts:profile', kwargs={'username': user_name_2}),
        }
        for number, reverse_ in reverses.items():
            with self.subTest(number=number):
                response = self.authorized_client.get(reverse_)
                self.assertNotIn(self.post, response.context['page_obj'])

    def index_page_cache(self):
        """Записи на главной странице сохраняются в кэш"""
        cache_1 = self.authorized_client.get(reverse('posts:index')).content
        self.post.delete()
        cache_2 = self.authorized_client.get(reverse('posts:index')).content
        cache.clear()
        cache_3 = self.authorized_client.get(reverse('posts:index')).content
        self.assertEqual(cache_1, cache_2)
        self.assertNotEqual(cache_1, cache_3)

    def test_authorized_user_follow_and_unfollow_authors(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок"""
        user_name_2 = self.user_2.username
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': user_name_2}))
        self.assertTrue(Follow.objects.filter(
            author=self.user_2, user=self.user).exists())
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': user_name_2}))
        self.assertFalse(Follow.objects.filter(
            author=self.user_2, user=self.user).exists())

    def test_post_appear_on_follower_pages(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(user=self.user, author=self.user_2)
        self.post_2 = Post.objects.create(
            author=self.user_2,
            text='Тестовый текст 2',
            group=self.group,
        )
        response = self.authorized_client.get('/follow/')
        self.assertIn(self.post_2, response.context['page_obj'])
        response = self.authorized_client_2.get('/follow/')
        self.assertNotIn(self.post_2, response.context['page_obj'])


class TaskPagesTests_2(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user_2 = User.objects.create_user(username='AnotherAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Описание тестовой группы'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group-slug-2',
            description='Описание тестовой группы'
        )
        batch_size = 100
        objs_1 = (Post(author=cls.user_2, text=f'Тестовый текст {i}',
                       group=cls.group_2) for i in range(0, 13))
        objs_2 = (Post(author=cls.user, text=f'Тестовый текст {i}',
                       group=cls.group) for i in range(14, 27))
        objs = chain(objs_1, objs_2)
        while True:
            batch = list(islice(objs, batch_size))
            if not batch:
                break
            Post.objects.bulk_create(batch, batch_size)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_pages_contains_correct_records_amount(self):
        """Paginator корректно формирует страницы."""
        group_slug = self.group.slug
        user_name = self.user.username
        reverses = {
            reverse('posts:index'): 10,
            reverse('posts:group_list', kwargs={'slug': group_slug}): 3,
            reverse('posts:profile', kwargs={'username': user_name}): 3,
        }
        for reverse_, numbers in reverses.items():
            with self.subTest(reverse_=reverse_):
                response = self.authorized_client.get(reverse_)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.authorized_client.get(reverse_ + '?page=2')
                self.assertEqual(len(response.context['page_obj']), numbers)
