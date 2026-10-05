from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Profile(TimeStampedModel):
    THEME_CHOICES = [('light', 'Світла'), ('dark', 'Темна'), ('orange', 'Помаранчева')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    specialization = models.CharField(max_length=120, blank=True)
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='orange')

    def __str__(self):
        return f'Профіль {self.user}'


class Course(TimeStampedModel):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    STATUS_CHOICES = [(DRAFT, 'Чернетка'), (PUBLISHED, 'Опубліковано'), (ARCHIVED, 'Архів')]
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    cover_image_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'course'
            slug = base
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f'{base}-{counter}'
            self.slug = slug
        if self.status == self.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class CourseMaterial(TimeStampedModel):
    TYPE_CHOICES = [('text', 'Текст'), ('file', 'Файл'), ('image', 'Зображення'), ('link', 'Посилання'), ('video', 'Відео')]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=255)
    material_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    text_content = models.TextField(blank=True)
    file_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    external_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def clean(self):
        requirements = {
            'text': self.text_content,
            'file': self.file_url,
            'image': self.image_url,
            'link': self.external_url,
            'video': self.external_url,
        }
        if self.material_type and not requirements.get(self.material_type):
            raise ValidationError('Заповніть поле, яке відповідає типу матеріалу.')

    def __str__(self):
        return self.title


class Test(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    passing_score = models.PositiveIntegerField(default=60)

    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:80]


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class TestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-finished_at']


class CourseEnrollment(models.Model):
    STARTED = 'started'
    COMPLETED = 'completed'
    STATUS_CHOICES = [(STARTED, 'Розпочато'), (COMPLETED, 'Завершено')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STARTED)

    class Meta:
        unique_together = ('user', 'course')


class MaterialProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='material_progress')
    material = models.ForeignKey(CourseMaterial, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'material')


class JobVacancy(TimeStampedModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_vacancies')
    title = models.CharField(max_length=255)
    clinic_name = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    short_description = models.TextField()
    full_description = models.TextField()
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    contact_info = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class InternshipPost(TimeStampedModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='internship_posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    image_url = models.URLField(blank=True)

    def rating(self):
        pluses = self.votes.filter(vote_type=InternshipVote.PLUS).count()
        minuses = self.votes.filter(vote_type=InternshipVote.MINUS).count()
        return pluses - minuses

    def __str__(self):
        return self.title


class InternshipVote(models.Model):
    PLUS = 'plus'
    MINUS = 'minus'
    VOTE_CHOICES = [(PLUS, '+'), (MINUS, '-')]
    post = models.ForeignKey(InternshipPost, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='internship_votes')
    vote_type = models.CharField(max_length=10, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')


class UserPost(TimeStampedModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    image_url = models.URLField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CalendarEvent(TimeStampedModel):
    TYPE_CHOICES = [('webinar', 'Вебінар'), ('external_course', 'Зовнішній курс'), ('internal_course', 'Курс Dentoria'), ('personal', 'Особиста'), ('other', 'Інше')]
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    external_url = models.URLField(blank=True)
    related_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='calendar_events')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ['starts_at']

    def clean(self):
        if self.ends_at and self.starts_at and self.ends_at < self.starts_at:
            raise ValidationError('Дата завершення не може бути раніше дати початку.')

    def __str__(self):
        return self.title


class Comment(TimeStampedModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(UserPost, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    internship_post = models.ForeignKey(InternshipPost, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    content = models.TextField()

    def clean(self):
        if bool(self.post) == bool(self.internship_post):
            raise ValidationError('Коментар має належати рівно одному посту.')
