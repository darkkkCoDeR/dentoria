from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.db.models import Avg, Count, F, Max, Q, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.views.decorators.http import require_POST

from .forms import (
    CalendarEventForm,
    CourseForm,
    CourseMaterialForm,
    InternshipPostForm,
    JobVacancyForm,
    ProfileForm,
    RegisterForm,
    TestForm,
    UserPostForm,
)
from .models import (
    CalendarEvent,
    Course,
    CourseEnrollment,
    CourseMaterial,
    InternshipPost,
    InternshipVote,
    JobVacancy,
    MaterialProgress,
    Test,
    TestAttempt,
    UserPost,
)


class DentoriaLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = AuthenticationForm


def send_activation_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_url = request.build_absolute_uri(reverse('activate', args=[uid, token]))
    send_mail(
        'Активація Dentoria',
        f'Перейдіть за посиланням для активації акаунта: {activation_url}',
        None,
        [user.email],
        fail_silently=False,
    )


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.email = form.cleaned_data['email']
            user.save()
            send_activation_email(request, user)
            messages.success(request, 'Реєстрація успішна. Перевірте email для активації.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'Акаунт активовано.')
        return redirect('home')
    messages.error(request, 'Посилання активації недійсне або застаріле.')
    return redirect('login')


@login_required
def resend_activation(request):
    if request.user.is_active:
        return redirect('home')
    send_activation_email(request, request.user)
    messages.success(request, 'Лист активації надіслано повторно.')
    return redirect('login')


def active_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_active:
            messages.warning(request, 'Спочатку активуйте акаунт через email.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@active_required
def home(request):
    return render(request, 'home.html', {
        'courses_count': Course.objects.filter(status=Course.PUBLISHED).count(),
        'jobs_count': JobVacancy.objects.filter(is_active=True).count(),
        'events_count': CalendarEvent.objects.filter(Q(is_public=True) | Q(author=request.user)).count(),
    })


@active_required
def profile(request):
    return render(request, 'accounts/profile.html')


@active_required
def profile_edit(request):
    profile_obj = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile_obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль оновлено.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile_obj, user=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


@active_required
def course_list(request):
    courses = Course.objects.filter(status=Course.PUBLISHED).select_related('author')
    return render(request, 'courses/course_list.html', {'courses': courses})


@active_required
def my_courses(request):
    courses = Course.objects.filter(author=request.user)
    return render(request, 'courses/my_courses.html', {'courses': courses})


@active_required
def course_create(request):
    return save_course(request)


@active_required
def course_edit(request, slug):
    course = get_course_for_owner(request, slug)
    return save_course(request, course)


def save_course(request, course=None):
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course_obj = form.save(commit=False)
            if course_obj.pk is None:
                course_obj.author = request.user
            course_obj.save()
            messages.success(request, 'Курс збережено.')
            return redirect('course_detail', slug=course_obj.slug)
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/course_form.html', {'form': form, 'course': course})


def get_course_for_owner(request, slug):
    if request.user.is_staff:
        return get_object_or_404(Course, slug=slug)
    return get_object_or_404(Course, slug=slug, author=request.user)


@active_required
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.status != Course.PUBLISHED and course.author != request.user and not request.user.is_staff:
        messages.error(request, 'Цей курс ще не опубліковано.')
        return redirect('course_list')
    CourseEnrollment.objects.get_or_create(user=request.user, course=course)
    return render(request, 'courses/course_detail.html', {'course': course})


@active_required
@require_POST
def course_publish(request, slug):
    course = get_course_for_owner(request, slug)
    course.status = Course.PUBLISHED
    course.published_at = timezone.now()
    course.save()
    messages.success(request, 'Курс оприлюднено.')
    return redirect('course_detail', slug=course.slug)


@active_required
def material_add(request, slug):
    course = get_course_for_owner(request, slug)
    if request.method == 'POST':
        form = CourseMaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course
            material.save()
            messages.success(request, 'Матеріал додано.')
            return redirect('course_detail', slug=course.slug)
    else:
        form = CourseMaterialForm()
    return render(request, 'courses/material_form.html', {'form': form, 'course': course})


@active_required
@require_POST
def material_complete(request, pk):
    material = get_object_or_404(CourseMaterial, pk=pk)
    MaterialProgress.objects.update_or_create(user=request.user, material=material, defaults={'is_completed': True, 'completed_at': timezone.now()})
    update_enrollment_progress(request.user, material.course)
    return redirect('course_detail', slug=material.course.slug)


def update_enrollment_progress(user, course):
    enrollment, _ = CourseEnrollment.objects.get_or_create(user=user, course=course)
    total = course.materials.count()
    done = MaterialProgress.objects.filter(user=user, material__course=course, is_completed=True).count()
    enrollment.progress = round(done * 100 / total) if total else 0
    if total and done >= total:
        enrollment.status = CourseEnrollment.COMPLETED
        enrollment.completed_at = timezone.now()
    enrollment.save()


@active_required
def test_add(request, slug):
    course = get_course_for_owner(request, slug)
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.course = course
            test.save()
            messages.info(request, 'Тест створено. Додайте питання через Django admin.')
            return redirect('course_detail', slug=course.slug)
    else:
        form = TestForm()
    return render(request, 'courses/test_form.html', {'form': form, 'course': course})


@active_required
def take_test(request, test_id):
    test = get_object_or_404(Test.objects.prefetch_related('questions__answers'), pk=test_id)
    if request.method == 'POST':
        max_score = test.questions.count()
        score = 0
        for question in test.questions.all():
            selected_ids = {int(value) for value in request.POST.getlist(f'question_{question.id}')}
            correct_ids = set(question.answers.filter(is_correct=True).values_list('id', flat=True))
            if selected_ids and selected_ids == correct_ids:
                score += 1
        percent = round(score * 100 / max_score) if max_score else 0
        TestAttempt.objects.create(user=request.user, test=test, score=percent, max_score=100, passed=percent >= test.passing_score)
        messages.success(request, f'Результат тесту: {percent}%.')
        return redirect('course_detail', slug=test.course.slug)
    return render(request, 'courses/take_test.html', {'test': test})


@active_required
def job_list(request):
    jobs = JobVacancy.objects.filter(is_active=True).select_related('author')
    return render(request, 'jobs/job_list.html', {'jobs': jobs})


@active_required
def job_detail(request, pk):
    return render(request, 'jobs/job_detail.html', {'job': get_object_or_404(JobVacancy, pk=pk)})


@active_required
def job_create(request):
    return save_job(request)


@active_required
def job_edit(request, pk):
    job = get_owned_or_admin(JobVacancy, request, pk)
    return save_job(request, job)


def save_job(request, job=None):
    if request.method == 'POST':
        form = JobVacancyForm(request.POST, instance=job)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.pk is None:
                obj.author = request.user
            obj.save()
            messages.success(request, 'Вакансію збережено.')
            return redirect('job_detail', pk=obj.pk)
    else:
        form = JobVacancyForm(instance=job)
    return render(request, 'jobs/job_form.html', {'form': form, 'job': job})



@active_required
def delete_owned(request, model, pk, success_url, label):
    obj = get_owned_or_admin(model, request, pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, f'{label} видалено.')
        return redirect(success_url)
    return render(request, 'confirm_delete.html', {'object': obj, 'label': label, 'cancel_url': success_url})

def get_owned_or_admin(model, request, pk):
    if request.user.is_staff:
        return get_object_or_404(model, pk=pk)
    return get_object_or_404(model, pk=pk, author=request.user)


@active_required
def internship_list(request):
    posts = InternshipPost.objects.annotate(
        plus_count=Count('votes', filter=Q(votes__vote_type=InternshipVote.PLUS)),
        minus_count=Count('votes', filter=Q(votes__vote_type=InternshipVote.MINUS)),
    ).annotate(rating_value=F('plus_count') - F('minus_count')).order_by('-rating_value', '-created_at')
    return render(request, 'internship/post_list.html', {'posts': posts})


@active_required
def internship_detail(request, pk):
    return render(request, 'internship/post_detail.html', {'post': get_object_or_404(InternshipPost, pk=pk)})


@active_required
def internship_create(request):
    return save_internship(request)


@active_required
def internship_edit(request, pk):
    return save_internship(request, get_owned_or_admin(InternshipPost, request, pk))


def save_internship(request, post=None):
    if request.method == 'POST':
        form = InternshipPostForm(request.POST, instance=post)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.pk is None:
                obj.author = request.user
            obj.save()
            messages.success(request, 'Пост збережено.')
            return redirect('internship_detail', pk=obj.pk)
    else:
        form = InternshipPostForm(instance=post)
    return render(request, 'internship/post_form.html', {'form': form, 'post': post})


@active_required
def internship_vote(request, pk, vote_type):
    post = get_object_or_404(InternshipPost, pk=pk)
    if vote_type not in {InternshipVote.PLUS, InternshipVote.MINUS}:
        messages.error(request, 'Некоректний голос.')
    else:
        vote, created = InternshipVote.objects.get_or_create(post=post, user=request.user, defaults={'vote_type': vote_type})
        if not created and vote.vote_type == vote_type:
            vote.delete()
        else:
            vote.vote_type = vote_type
            vote.save()
    return redirect('internship')


@active_required
def post_list(request):
    return render(request, 'posts/post_list.html', {'posts': UserPost.objects.select_related('author')})


@active_required
def post_detail(request, pk):
    return render(request, 'posts/post_detail.html', {'post': get_object_or_404(UserPost, pk=pk)})


@active_required
def post_create(request):
    return save_post(request)


@active_required
def post_edit(request, pk):
    return save_post(request, get_owned_or_admin(UserPost, request, pk))


def save_post(request, post=None):
    if request.method == 'POST':
        form = UserPostForm(request.POST, instance=post)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.pk is None:
                obj.author = request.user
            obj.save()
            messages.success(request, 'Пост збережено.')
            return redirect('post_detail', pk=obj.pk)
    else:
        form = UserPostForm(instance=post)
    return render(request, 'posts/post_form.html', {'form': form, 'post': post})


@active_required
def calendar_list(request):
    events = CalendarEvent.objects.filter(Q(is_public=True) | Q(author=request.user)).select_related('author', 'related_course')
    return render(request, 'calendar/event_list.html', {'events': events})


@active_required
def event_create(request):
    return save_event(request)


@active_required
def event_edit(request, pk):
    return save_event(request, get_owned_or_admin(CalendarEvent, request, pk))


def save_event(request, event=None):
    if request.method == 'POST':
        form = CalendarEventForm(request.POST, instance=event)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.pk is None:
                obj.author = request.user
            obj.save()
            messages.success(request, 'Подію збережено.')
            return redirect('calendar')
    else:
        form = CalendarEventForm(instance=event)
    return render(request, 'calendar/event_form.html', {'form': form, 'event': event})


@active_required
def progress_dashboard(request):
    enrollments = CourseEnrollment.objects.filter(user=request.user).select_related('course')
    attempts = TestAttempt.objects.filter(user=request.user)
    return render(request, 'progress/dashboard.html', {
        'enrollments': enrollments,
        'started_count': enrollments.count(),
        'completed_count': enrollments.filter(status=CourseEnrollment.COMPLETED).count(),
        'avg_score': attempts.aggregate(value=Avg('score'))['value'] or 0,
        'attempts_count': attempts.count(),
        'overall_progress': enrollments.aggregate(value=Avg('progress'))['value'] or 0,
        'recent_attempts': attempts.select_related('test', 'test__course')[:5],
    })


@active_required
def course_progress(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(CourseEnrollment, user=request.user, course=course)
    total_materials = course.materials.count()
    completed_materials = MaterialProgress.objects.filter(user=request.user, material__course=course, is_completed=True).count()
    attempts = TestAttempt.objects.filter(user=request.user, test__course=course)
    return render(request, 'progress/course_progress.html', {
        'course': course,
        'enrollment': enrollment,
        'total_materials': total_materials,
        'completed_materials': completed_materials,
        'attempts': attempts,
        'best_score': attempts.aggregate(value=Max('score'))['value'] or 0,
        'last_attempt': attempts.first(),
    })


@active_required
def job_delete(request, pk):
    return delete_owned(request, JobVacancy, pk, 'job_list', 'Вакансію')


@active_required
def internship_delete(request, pk):
    return delete_owned(request, InternshipPost, pk, 'internship', 'Пост інтернатури')


@active_required
def post_delete(request, pk):
    return delete_owned(request, UserPost, pk, 'post_list', 'Пост')


@active_required
def event_delete(request, pk):
    return delete_owned(request, CalendarEvent, pk, 'calendar', 'Подію')
