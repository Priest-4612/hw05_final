from django.test import Client, TestCase


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.template_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }

    def test_urls_exists_at_desired_location(self):
        """Проверка доступности адресов /about/***/."""
        for template, adress in self.template_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """Проверка шаблонов для адресов /about/***/."""
        for template, adress in self.template_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
