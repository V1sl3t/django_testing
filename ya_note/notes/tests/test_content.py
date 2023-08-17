from django.test import TestCase
from notes.models import Note
from django.urls import reverse
from django.contrib.auth import get_user_model


User = get_user_model()


class TestDetailPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       author=cls.author)

    def test_authorized_client_has_form(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', {'slug': self.note.slug}),
        )
        for name, kwargs in urls:
            self.client.force_login(self.author)
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                response = self.client.get(url)
                self.assertIn('form', response.context)

    def test_notes_list_for_different_users(self):
        users_note_in_list = (
            (self.author, True),
            (self.reader, False),
        )
        for user, note_in_list in users_note_in_list:
            self.client.force_login(user)
            with self.subTest(user=user, note_in_list=note_in_list):
                url = reverse('notes:list')
                response = self.client.get(url)
                object_list = response.context['object_list']
                status = self.note in object_list
                self.assertEqual(status, note_in_list)
