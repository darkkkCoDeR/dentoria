from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory

from .models import (
    AnswerOption,
    CalendarEvent,
    Course,
    CourseMaterial,
    InternshipPost,
    JobVacancy,
    Profile,
    Question,
    Test,
    UserPost,
)


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            css_class = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            if isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} {css_class}'.strip()


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(label='Email')
    first_name = forms.CharField(label="Ім'я", required=False)
    last_name = forms.CharField(label='Прізвище', required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Користувач з таким email вже існує.')
        return email


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    first_name = forms.CharField(label="Ім'я", required=False)
    last_name = forms.CharField(label='Прізвище', required=False)
    email = forms.EmailField(label='Email')

    class Meta:
        model = Profile
        fields = ['avatar_url', 'bio', 'specialization', 'theme']
        labels = {
            'avatar_url': 'Cloudinary URL аватара',
            'bio': 'Про себе',
            'specialization': 'Спеціалізація',
            'theme': 'Тема',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = self.user.first_name
        self.fields['last_name'].initial = self.user.last_name
        self.fields['email'].initial = self.user.email
        self._apply_bootstrap()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Користувач з таким email вже існує.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        if commit:
            self.user.save()
            profile.save()
        return profile


class CourseForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'cover_image_url', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class CourseMaterialForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = ['title', 'material_type', 'text_content', 'file_url', 'image_url', 'external_url', 'order']
        widgets = {'text_content': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class TestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'passing_score']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class QuestionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class AnswerOptionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ['text', 'is_correct']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


AnswerOptionFormSet = modelformset_factory(AnswerOption, form=AnswerOptionForm, extra=4, can_delete=True)


class JobVacancyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = JobVacancy
        exclude = ['author']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class InternshipPostForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = InternshipPost
        fields = ['title', 'content', 'image_url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class UserPostForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = UserPost
        fields = ['title', 'content', 'image_url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class CalendarEventForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CalendarEvent
        exclude = ['author']
        widgets = {
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
