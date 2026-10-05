from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import CalendarEventForm, CourseMaterialForm, RegisterForm
from .models import Course, InternshipPost, InternshipVote


class DentoriaModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='doctor', email='doctor@example.com', password='pass12345')

    def test_profile_created_for_user(self):
        self.assertEqual(self.user.profile.theme, 'orange')

    def test_course_slug_is_generated_and_publish_sets_timestamp(self):
        course = Course.objects.create(author=self.user, title='Dental Basics', status=Course.PUBLISHED)
        self.assertEqual(course.slug, 'dental-basics')
        self.assertIsNotNone(course.published_at)

    def test_internship_vote_is_unique_per_user_and_post(self):
        post = InternshipPost.objects.create(author=self.user, title='Internship', content='Text')
        InternshipVote.objects.create(post=post, user=self.user, vote_type=InternshipVote.PLUS)
        with self.assertRaises(Exception):
            InternshipVote.objects.create(post=post, user=self.user, vote_type=InternshipVote.MINUS)


class DentoriaFormTests(TestCase):
    def test_register_form_requires_unique_email(self):
        User.objects.create_user(username='u1', email='same@example.com', password='pass12345')
        form = RegisterForm(data={
            'username': 'u2',
            'email': 'same@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_material_form_requires_matching_url_field(self):
        form = CourseMaterialForm(data={'title': 'PDF', 'material_type': 'file', 'order': 1})
        self.assertFalse(form.is_valid())

    def test_calendar_form_rejects_invalid_dates(self):
        now = timezone.now()
        form = CalendarEventForm(data={
            'title': 'Webinar',
            'description': 'Demo',
            'event_type': 'webinar',
            'starts_at': now.strftime('%Y-%m-%dT%H:%M'),
            'ends_at': (now - timezone.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            'is_public': 'on',
        })
        self.assertFalse(form.is_valid())


class DentoriaViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='active', email='active@example.com', password='pass12345', is_active=True)

    def test_course_list_requires_login(self):
        response = self.client.get(reverse('course_list'))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_open_home(self):
        self.client.login(username='active', password='pass12345')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dentoria')

    def test_draft_course_visible_to_author(self):
        course = Course.objects.create(author=self.user, title='Draft Course')
        self.client.login(username='active', password='pass12345')
        response = self.client.get(reverse('course_detail', args=[course.slug]))
        self.assertEqual(response.status_code, 200)
