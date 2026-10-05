from django.contrib import admin

from .models import (
    AnswerOption,
    CalendarEvent,
    Comment,
    Course,
    CourseEnrollment,
    CourseMaterial,
    InternshipPost,
    InternshipVote,
    JobVacancy,
    MaterialProgress,
    Profile,
    Question,
    Test,
    TestAttempt,
    UserPost,
)


class CourseMaterialInline(admin.TabularInline):
    model = CourseMaterial
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'theme', 'updated_at')
    search_fields = ('user__username', 'user__email', 'specialization')
    list_filter = ('theme',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'published_at', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    list_filter = ('status', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CourseMaterialInline]


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'passing_score')
    search_fields = ('title', 'course__title')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'order')
    search_fields = ('text', 'test__title')
    inlines = [AnswerOptionInline]


@admin.register(JobVacancy)
class JobVacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'clinic_name', 'city', 'author', 'is_active', 'created_at')
    search_fields = ('title', 'clinic_name', 'city')
    list_filter = ('is_active', 'city')


@admin.register(InternshipPost)
class InternshipPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content', 'author__username')


@admin.register(InternshipVote)
class InternshipVoteAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'vote_type', 'created_at')
    list_filter = ('vote_type',)


@admin.register(UserPost)
class UserPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content', 'author__username')


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'event_type', 'starts_at', 'is_public')
    search_fields = ('title', 'description', 'author__username')
    list_filter = ('event_type', 'is_public')


admin.site.register(CourseMaterial)
admin.site.register(CourseEnrollment)
admin.site.register(MaterialProgress)
admin.site.register(AnswerOption)
admin.site.register(TestAttempt)
admin.site.register(Comment)
