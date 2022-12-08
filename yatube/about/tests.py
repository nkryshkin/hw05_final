from django.contrib.auth import get_user_model
from django.test import TestCase, Client


User = get_user_model()


class TaskURLTests(TestCase):
    def setUp(cls):
        cls.guest_client = Client()

    def test_urls_exists_at_desired_location_guest(cls):
        """Доступность страниц анонимному пользователю."""
        urls = {
            '/about/tech/': 'OK',
            '/about/author/': 'OK',
        }
        for address, code in urls.items():
            with cls.subTest(address=address):
                response = cls.guest_client.get(address)
                cls.assertEqual(response.reason_phrase, code)

    def test_urls_uses_correct_template(cls):
        """URL-адрес использует соответствующий шаблон."""
        templates = {
            '/about/tech/': 'about/tech.html',
            '/about/author/': 'about/author.html',
        }
        for address, template in templates.items():
            with cls.subTest(address=address):
                response = cls.guest_client.get(address)
                cls.assertTemplateUsed(response, template)
