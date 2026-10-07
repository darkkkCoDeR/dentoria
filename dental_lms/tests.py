from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import CalendarEventForm, CourseMaterialForm, LoginForm, RegisterForm
from .models import CalendarEvent, Course, InternshipPost, InternshipVote, JobVacancy, UserPost


class DentoriaSeedCommandTests(TestCase):
    def test_production_safe_seed_creates_dental_content_without_login_account(self):
        call_command('seed_demo_data', '--production-safe', stdout=StringIO())
        call_command('seed_demo_data', '--production-safe', stdout=StringIO())

        author = User.objects.get(username='dentoria_content')
        self.assertFalse(author.is_active)
        self.assertFalse(author.is_staff)
        self.assertFalse(author.is_superuser)
        self.assertFalse(author.has_usable_password())
        self.assertFalse(User.objects.filter(username='admin_demo').exists())
        self.assertEqual(Course.objects.filter(author=author).count(), 4)
        self.assertEqual(JobVacancy.objects.filter(author=author).count(), 3)
        self.assertEqual(InternshipPost.objects.filter(author=author).count(), 3)
        self.assertEqual(UserPost.objects.filter(author=author).count(), 4)
        self.assertEqual(CalendarEvent.objects.filter(author=author).count(), 4)
        self.assertEqual(
            Course.objects.filter(
                author=author,
                cover_image_url__startswith='/static/img/dentoria-',
            ).count(),
            3,
        )
        self.assertEqual(
            UserPost.objects.filter(
                author=author,
                image_url='/static/img/dentoria-post.svg',
            ).count(),
            4,
        )


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
    def test_login_form_uses_styled_fields(self):
        form = LoginForm()
        self.assertIn('form-control', form.fields['username'].widget.attrs['class'])
        self.assertEqual(form.fields['password'].widget.attrs['autocomplete'], 'current-password')

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

    def test_login_page_has_contextual_submit_button(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '>Увійти</button>')

    def test_register_page_has_contextual_submit_button(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '>Створити акаунт</button>')

    @override_settings(
        SITE_URL='https://dentoria.onrender.com',
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_activation_email_uses_configured_site_url(self):
        response = self.client.post(reverse('register'), {
            'username': 'site-url-user',
            'email': 'site-url-user@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertRedirects(response, reverse('login'))
        self.assertIn('https://dentoria.onrender.com/accounts/activate/', mail.outbox[0].body)
        self.assertNotIn('127.0.0.1', mail.outbox[0].body)

    @patch('dental_lms.views.send_activation_email', side_effect=OSError('Network is unreachable'))
    def test_register_handles_activation_email_network_error(self, _send_activation_email):
        with self.assertLogs('dental_lms.views', level='ERROR'):
            response = self.client.post(reverse('register'), {
                'username': 'new-user',
                'email': 'new-user@example.com',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Не вдалося надіслати лист активації.')
        self.assertFalse(User.objects.filter(username='new-user').exists())

    @override_settings(REQUIRE_EMAIL_ACTIVATION=False)
    @patch('dental_lms.views.send_activation_email')
    def test_register_activates_user_without_email_in_demo_mode(self, send_activation_email):
        response = self.client.post(reverse('register'), {
            'username': 'demo-user',
            'email': 'demo-user@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.get(username='demo-user').is_active)
        send_activation_email.assert_not_called()

    def test_authenticated_user_can_open_home(self):
        self.client.login(username='active', password='pass12345')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dentoria')

    def test_theme_select_submits_without_separate_button(self):
        self.client.login(username='active', password='pass12345')
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'data-auto-submit')
        self.assertNotContains(response, '>Тема</button>')

    def test_draft_course_visible_to_author(self):
        course = Course.objects.create(author=self.user, title='Draft Course')
        self.client.login(username='active', password='pass12345')
        response = self.client.get(reverse('course_detail', args=[course.slug]))
        self.assertEqual(response.status_code, 200)


class DentoriaFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='filter-user',
            email='filter@example.com',
            password='pass12345',
            is_active=True,
        )
        self.client.login(username='filter-user', password='pass12345')

        self.ai_course = Course.objects.create(
            author=self.user,
            title='AI діагностика',
            description='Цифровий аналіз знімків',
            status=Course.PUBLISHED,
        )
        self.endo_course = Course.objects.create(
            author=self.user,
            title='Основи ендодонтії',
            description='Робота з каналами',
            status=Course.PUBLISHED,
        )
        self.draft_course = Course.objects.create(
            author=self.user,
            title='Чернетка курсу',
            status=Course.DRAFT,
        )

        self.active_job = JobVacancy.objects.create(
            author=self.user,
            title='Асистент стоматолога',
            clinic_name='Dentoria Kyiv',
            city='Київ',
            short_description='Робота в команді',
            full_description='Повна зайнятість',
            contact_info='kyiv@example.com',
            is_active=True,
        )
        self.inactive_job = JobVacancy.objects.create(
            author=self.user,
            title='Лікар-інтерн',
            clinic_name='Dentoria Lviv',
            city='Львів',
            short_description='Програма інтернатури',
            full_description='Навчання у клініці',
            contact_info='lviv@example.com',
            is_active=False,
        )

        InternshipPost.objects.create(author=self.user, title='Чекліст інтерна', content='Перший прийом')
        InternshipPost.objects.create(author=self.user, title='Телестоматологія', content='Онлайн-консультації')
        UserPost.objects.create(author=self.user, title='Системне здоровʼя', content='Оральне здоровʼя')
        UserPost.objects.create(author=self.user, title='Цифровий протокол', content='Новини технологій')

        now = timezone.now()
        CalendarEvent.objects.create(
            author=self.user,
            title='AI вебінар',
            event_type='webinar',
            starts_at=now,
            ends_at=now + timezone.timedelta(hours=1),
            is_public=True,
        )
        CalendarEvent.objects.create(
            author=self.user,
            title='Особиста зустріч',
            event_type='personal',
            starts_at=now,
            ends_at=now + timezone.timedelta(hours=1),
            is_public=False,
        )

    def test_course_catalog_search_filters_results(self):
        response = self.client.get(reverse('course_list'), {'q': 'AI'})
        self.assertContains(response, self.ai_course.title)
        self.assertNotContains(response, self.endo_course.title)
        self.assertNotContains(response, 'name="status"')

    def test_my_courses_status_filter_filters_results(self):
        response = self.client.get(reverse('my_courses'), {'status': Course.DRAFT})
        self.assertContains(response, self.draft_course.title)
        self.assertNotContains(response, self.ai_course.title)

    def test_job_filters_support_city_and_all_statuses(self):
        response = self.client.get(reverse('job_list'), {'city': 'львів', 'active': ''})
        self.assertContains(response, self.inactive_job.title)
        self.assertNotContains(response, self.active_job.title)

    def test_internship_search_filters_results(self):
        response = self.client.get(reverse('internship'), {'q': 'Чекліст'})
        self.assertContains(response, 'Чекліст інтерна')
        self.assertNotContains(response, 'Телестоматологія')

    def test_post_search_filters_results(self):
        response = self.client.get(reverse('post_list'), {'q': 'системне'})
        self.assertContains(response, 'Системне здоровʼя')
        self.assertNotContains(response, 'Цифровий протокол')

    def test_calendar_type_filter_filters_results(self):
        response = self.client.get(reverse('calendar'), {'event_type': 'webinar'})
        self.assertContains(response, 'AI вебінар')
        self.assertNotContains(response, 'Особиста зустріч')
