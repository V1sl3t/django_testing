from django.test import TestCase
from http import HTTPStatus
from django.urls import reverse
from notes.models import Note
from django.contrib.auth import get_user_model

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Другой автор')
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       author=cls.author)

    def test_pages_availability(self):
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_client(self):
        urls = (
            'notes:add',
            'notes:success',
            'notes:list',
        )
        for name in urls:
            self.client.force_login(self.author)
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note__edit_delete_detail(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:edit', 'notes:delete', 'notes:detail'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, kwargs={'slug': self.note.slug})
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_pages_redirect(self):
        login_url = reverse('users:login')
        urls = (
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
            ('notes:delete', {'slug': self.note.slug}),
            ('notes:edit', {'slug': self.note.slug}),
            ('notes:detail', {'slug': self.note.slug}),
        )
        for name, kwargs in urls:
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
