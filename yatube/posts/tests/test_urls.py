from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='HasNoName')
        cls.user_2 = User.objects.create_user(username='AnotherAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Описание тестовой группы'
        )
        cls.post_1 = Post.objects.create(
            author=cls.user_1,
            text='Тестовый текст',
            group=cls.group
        )
        cls.post_2 = Post.objects.create(
            author=cls.user_2,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(cls):
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_1)

    def test_urls_exists_at_desired_location_guest(cls):
        """Доступность страниц анонимному пользователю."""
        urls = {
            '/': 'OK',
            f'/group/{cls.post_1.group.slug}/': 'OK',
            f'/profile/{cls.post_1.author.username}/': 'OK',
            f'/posts/{cls.post_1.id}/': 'OK',
            f'/posts/{cls.post_1.id}/edit/': 'Found',
            '/create/': 'Found',
            '/unexisting_page/': 'Not Found'
        }
        for address, code in urls.items():
            with cls.subTest(address=address):
                response = cls.guest_client.get(address)
                cls.assertEqual(response.reason_phrase, code)

    def test_urls_exists_at_desired_location_authorised_user(cls):
        """Доступность страниц авторизованному пользователю."""
        urls = {
            '/': 'OK',
            f'/group/{cls.post_1.group.slug}/': 'OK',
            f'/profile/{cls.post_1.author.username}/': 'OK',
            f'/posts/{cls.post_1.id}/': 'OK',
            f'/posts/{cls.post_1.id}/edit/': 'OK',
            f'/posts/{cls.post_2.id}/edit/': 'Found',
            '/create/': 'OK',
            '/unexisting_page/': 'Not Found'
        }
        for address, code in urls.items():
            with cls.subTest(address=address):
                response = cls.authorized_client.get(address)
                cls.assertEqual(response.reason_phrase, code)

    def test_redirect_post_create_post_edit(cls):
        """Перенаправление авторизованных и неавторизованных
        пользователей со страниц редактирования и создания постов"""
        post_1_id = cls.post_1.id
        post_2_id = cls.post_2.id
        response = cls.guest_client.get('/create/')
        cls.assertRedirects(response, '/auth/login/?next=/create/')
        response = cls.guest_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_1_id}))
        cls.assertRedirects(response, (
            f'/auth/login/?next=/posts/{post_1_id}/edit/'))
        response = cls.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_2_id}))
        cls.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post_2_id}))

    def test_urls_uses_correct_template(cls):
        """URL-адрес использует соответствующий шаблон."""
        templates = {
            '/': 'posts/index.html',
            f'/group/{cls.post_1.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post_1.author.username}/': 'posts/profile.html',
            f'/posts/{cls.post_1.id}/': 'posts/post_detail.html',
            f'/posts/{cls.post_1.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/wrong_adress/': 'core/404.html'
        }
        for address, template in templates.items():
            with cls.subTest(address=address):
                response = cls.authorized_client.get(address)
                cls.assertTemplateUsed(response, template)
