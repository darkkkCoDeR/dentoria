from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
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
            if isinstance(field.widget, forms.FileInput):
                css_class = 'form-control'
            if isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} {css_class}'.strip()


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логін'
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Введіть логін',
            'autocomplete': 'username',
        })
        self.fields['password'].label = 'Пароль'
        self.fields['password'].widget.attrs.update({
            'placeholder': 'Введіть пароль',
            'autocomplete': 'current-password',
        })
        self._apply_bootstrap()


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(label='Email')
    first_name = forms.CharField(label="Ім'я", required=False)
    last_name = forms.CharField(label='Прізвище', required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логін'
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Оберіть логін',
            'autocomplete': 'username',
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'name@example.com',
            'autocomplete': 'email',
        })
        self.fields['first_name'].widget.attrs.update({
            'placeholder': "Ваше ім'я",
            'autocomplete': 'given-name',
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Ваше прізвище',
            'autocomplete': 'family-name',
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Створіть надійний пароль',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Повторіть пароль',
            'autocomplete': 'new-password',
        })
        self._apply_bootstrap()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Користувач з таким email вже існує.')
        return email


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    avatar_upload = forms.ImageField(label='Завантажити аватар', required=False)
    first_name = forms.CharField(label="Ім'я", required=False)
    last_name = forms.CharField(label='Прізвище', required=False)
    email = forms.EmailField(label='Email')

    class Meta:
        model = Profile
        fields = ['avatar_url', 'bio', 'specialization', 'theme']
        labels = {
            'avatar_url': 'Cloudinary URL аватара або буде заповнений після upload',
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
    cover_image_upload = forms.ImageField(label='Завантажити обкладинку', required=False)

    class Meta:
        model = Course
        fields = ['title', 'description', 'cover_image_url', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class CourseMaterialForm(BootstrapFormMixin, forms.ModelForm):
    file_upload = forms.FileField(label='Завантажити файл', required=False)
    image_upload = forms.ImageField(label='Завантажити зображення', required=False)

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
    image_upload = forms.ImageField(label='Завантажити зображення', required=False)

    class Meta:
        model = InternshipPost
        fields = ['title', 'content', 'image_url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class UserPostForm(BootstrapFormMixin, forms.ModelForm):
    image_upload = forms.ImageField(label='Завантажити зображення', required=False)

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


class ThemeForm(BootstrapFormMixin, forms.Form):
    theme = forms.ChoiceField(label='Тема', choices=Profile.THEME_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class SearchFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(label='Пошук', required=False, widget=forms.TextInput(attrs={'placeholder': 'Ключові слова'}))
    sort = forms.ChoiceField(
        label='Сортування',
        required=False,
        choices=[('newest', 'Найновіші'), ('oldest', 'Найстаріші'), ('title', 'За назвою')],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class CourseCatalogFilterForm(SearchFilterForm):
    pass


class CourseFilterForm(SearchFilterForm):
    status = forms.ChoiceField(
        label='Статус',
        required=False,
        choices=[('', 'Усі статуси'), (Course.PUBLISHED, 'Опубліковані'), (Course.DRAFT, 'Чернетки'), (Course.ARCHIVED, 'Архів')],
    )


class JobFilterForm(SearchFilterForm):
    city = forms.CharField(label='Місто', required=False, widget=forms.TextInput(attrs={'placeholder': 'Напр. Київ'}))
    active = forms.ChoiceField(
        label='Стан',
        required=False,
        choices=[('', 'Усі'), ('active', 'Активні'), ('inactive', 'Неактивні')],
    )


class ContentFilterForm(SearchFilterForm):
    sort = forms.ChoiceField(
        label='Сортування',
        required=False,
        choices=[('newest', 'Найновіші'), ('oldest', 'Найстаріші'), ('title', 'За назвою')],
    )


class InternshipFilterForm(SearchFilterForm):
    sort = forms.ChoiceField(
        label='Сортування',
        required=False,
        choices=[('rating', 'За рейтингом'), ('newest', 'Найновіші'), ('oldest', 'Найстаріші'), ('title', 'За назвою')],
    )


class CalendarEventFilterForm(SearchFilterForm):
    event_type = forms.ChoiceField(label='Тип', required=False, choices=[('', 'Усі типи')] + CalendarEvent.TYPE_CHOICES)
    visibility = forms.ChoiceField(
        label='Видимість',
        required=False,
        choices=[('', 'Усі'), ('public', 'Публічні'), ('private', 'Приватні')],
    )
