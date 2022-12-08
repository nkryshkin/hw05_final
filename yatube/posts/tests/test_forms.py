import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
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
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Описание тестовой группы'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group-slug-2',
            description='Описание тестовой группы 2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(cls):
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_create_post(cls):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        user_name = cls.user.username
        group_id = cls.group.id
        user_id = cls.user.id
        post_image = cls.uploaded
        form_data = {
            'text': 'Тестовый текст номер 2',
            'group': group_id,
            'image': post_image
        }
        response = cls.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        cls.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': user_name}))
        cls.assertEqual(Post.objects.count(), post_count + 1)
        cls.assertTrue(
            Post.objects.filter(
                author=user_id,
                text=form_data['text'],
                group=group_id,
                image='posts/small.gif',
            ).exists()
        )

    def test_edit_post(cls):
        """Валидная форма изменяет запись в Post."""
        post_count = Post.objects.count()
        post_id = cls.post.id
        group_2_id = cls.group_2.id
        user_id = cls.user.id
        form_data = {
            'text': 'Тестовый текст номер 3',
            'group': group_2_id
        }
        response = cls.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        cls.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post_id}))
        cls.assertEqual(Post.objects.count(), post_count)
        cls.assertTrue(
            Post.objects.filter(
                id=post_id,
                author=user_id,
                text=form_data['text'],
                group=group_2_id
            ).exists()
        )

    def test_create_comment_authorised_user(cls):
        """Валидная форма создает комментарий - авторизованный
        пользователь."""
        comments_count = cls.post.comments.count()
        post_id = cls.post.id
        user_id = cls.user.id
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = cls.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        cls.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post_id}))
        cls.assertEqual(cls.post.comments.count(), comments_count + 1)
        cls.assertTrue(
            Comment.objects.filter(
                author_id=user_id,
                text=form_data['text'],
                post=post_id
            ).exists()
        )

    def test_create_comment(cls):
        """Неавторизованный пользователь не может оставить комментарий"""
        comments_count = cls.post.comments.count()
        post_id = cls.post.id
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = cls.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        cls.assertRedirects(
            response, f'/auth/login/?next=/posts/{post_id}/comment/')
        cls.assertEqual(cls.post.comments.count(), comments_count)
