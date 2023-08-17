from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note
from notes.forms import WARNING
from pytils.translit import slugify

User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TITLE = 'Title ноута'
    NOTE_TEXT = 'Текст ноута'
    NOTE_SLUG = 'ret'

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)
        cls.form_data = {'text': cls.NOTE_TEXT,
                         'title': cls.NOTE_TITLE,
                         'slug': cls.NOTE_SLUG,
                         }

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.form_data)
        redirect_url = reverse('notes:success')
        self.assertRedirects(response, redirect_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.user)

    def test_empty_slug(self):
        url = reverse('notes:add')
        self.form_data.pop('slug')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    NOTE_TEXT = 'Текст ноута'
    NOTE_TITLE = 'Title ноута'
    NOTE_SLUG = 'ret'
    NEW_NOTE_TEXT = 'Обновлённый текст ноута'
    NEW_NOTE_TITLE = 'Обновлённый Title ноута'

    @classmethod
    def setUpTestData(cls):
        cls.success_url = reverse('notes:success')
        cls.author = User.objects.create(username='Автор ноута')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            author=cls.author,
            text=cls.NOTE_TEXT,
            title=cls.NOTE_TITLE,
            slug=cls.NOTE_SLUG,
        )
        cls.edit_url = reverse('notes:edit', kwargs={'slug': cls.note.slug})
        cls.delete_url = reverse('notes:delete',
                                 kwargs={'slug': cls.note.slug}
                                 )
        cls.form_data = {'text': cls.NEW_NOTE_TEXT,
                         'title': cls.NEW_NOTE_TITLE,
                         'slug': cls.NOTE_SLUG,
                         }

    def test_not_unique_slug(self):
        url = reverse('notes:add')
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(response,
                             'form',
                             'slug',
                             errors=(self.note.slug + WARNING)
                             )
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_comment(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)

    def test_user_cant_edit_comment_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.title, self.NOTE_TITLE)
