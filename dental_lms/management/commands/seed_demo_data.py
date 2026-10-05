from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from dental_lms.models import (
    AnswerOption,
    CalendarEvent,
    Course,
    CourseEnrollment,
    CourseMaterial,
    InternshipPost,
    InternshipVote,
    JobVacancy,
    MaterialProgress,
    Question,
    Test,
    TestAttempt,
    UserPost,
)


class Command(BaseCommand):
    help = "Create demo Dentoria users and content for local manual testing."

    def handle(self, *args, **options):
        demo_password = "DemoPass123"
        admin = self._user("admin_demo", "admin@dentoria.test", demo_password, is_staff=True, is_superuser=True)
        teacher = self._user("teacher_demo", "teacher@dentoria.test", demo_password)
        student = self._user("student_demo", "student@dentoria.test", demo_password)
        intern = self._user("intern_demo", "intern@dentoria.test", demo_password)

        teacher.profile.specialization = "Терапевтична стоматологія"
        teacher.profile.bio = "Викладач Dentoria, автор базових курсів."
        teacher.profile.avatar_url = "https://res.cloudinary.com/demo/image/upload/sample.jpg"
        teacher.profile.theme = "orange"
        teacher.profile.save()

        student.profile.specialization = "Студент стоматології"
        student.profile.bio = "Тестовий студент для перевірки прогресу."
        student.profile.theme = "light"
        student.profile.save()

        course = self._course(
            author=teacher,
            title="Основи ендодонтії",
            description="Практичний вступ до діагностики, інструментації та пломбування кореневих каналів.",
            status=Course.PUBLISHED,
            cover_image_url="https://res.cloudinary.com/demo/image/upload/sample.jpg",
        )
        draft = self._course(
            author=teacher,
            title="Чернетка курсу з ортопедії",
            description="Курс ще готується і має бути видимим лише автору.",
            status=Course.DRAFT,
        )

        material_text = self._material(
            course=course,
            title="Вступний конспект",
            material_type="text",
            text_content="Ендодонтичне лікування починається з діагностики та ізоляції робочого поля.",
            order=1,
        )
        material_file = self._material(
            course=course,
            title="PDF чекліст інструментів",
            material_type="file",
            file_url="https://res.cloudinary.com/demo/raw/upload/sample.pdf",
            order=2,
        )
        self._material(
            course=course,
            title="Схема будови зуба",
            material_type="image",
            image_url="https://res.cloudinary.com/demo/image/upload/sample.jpg",
            order=3,
        )
        self._material(
            course=course,
            title="Вебінар з протоколу лікування",
            material_type="video",
            external_url="https://example.com/webinar/endodontics",
            order=4,
        )
        self._material(
            course=draft,
            title="План майбутнього курсу",
            material_type="text",
            text_content="Додати лекції, фото клінічних кейсів та фінальний тест.",
            order=1,
        )

        test = self._test(course, "Фінальний тест з ендодонтії", "Коротка перевірка базових понять.", 60)
        question = self._question(test, "Що потрібно зробити перед початком ендодонтичного лікування?", 1)
        self._answer(question, "Провести діагностику та ізоляцію", True)
        self._answer(question, "Одразу пломбувати канал", False)
        question_two = self._question(test, "Який матеріал є частиною навчального курсу?", 2)
        self._answer(question_two, "PDF чекліст інструментів", True)
        self._answer(question_two, "Рецепт кави", False)

        enrollment, _ = CourseEnrollment.objects.get_or_create(user=student, course=course)
        MaterialProgress.objects.update_or_create(
            user=student,
            material=material_text,
            defaults={"is_completed": True, "completed_at": timezone.now()},
        )
        MaterialProgress.objects.update_or_create(
            user=student,
            material=material_file,
            defaults={"is_completed": True, "completed_at": timezone.now()},
        )
        enrollment.progress = 50
        enrollment.save()
        TestAttempt.objects.get_or_create(
            user=student,
            test=test,
            defaults={"score": 75, "max_score": 100, "passed": True},
        )

        JobVacancy.objects.get_or_create(
            title="Асистент стоматолога",
            clinic_name="Dentoria Clinic",
            city="Київ",
            defaults={
                "author": intern,
                "short_description": "Позиція для молодого спеціаліста у дружній команді.",
                "full_description": "Робота з лікарем, підготовка кабінету, ведення базової документації.",
                "requirements": "Базові знання стоматології, уважність, бажання навчатися.",
                "responsibilities": "Підготовка інструментів, допомога під час прийому, стерилізація.",
                "conditions": "Гнучкий графік, наставництво, можливість професійного росту.",
                "contact_info": "hr@dentoria.test",
                "is_active": True,
            },
        )
        JobVacancy.objects.get_or_create(
            title="Лікар-інтерн",
            clinic_name="Orange Dental Hub",
            city="Львів",
            defaults={
                "author": teacher,
                "short_description": "Інтернатура з наставником і реальними клінічними кейсами.",
                "full_description": "Програма для інтернів з регулярним розбором кейсів.",
                "requirements": "Медична освіта, відповідальність, комунікабельність.",
                "responsibilities": "Участь у прийомах, ведення історій, навчальні зустрічі.",
                "conditions": "Часткова зайнятість, навчальні модулі, сертифікат.",
                "contact_info": "internship@dentoria.test",
                "is_active": True,
            },
        )

        internship_post = InternshipPost.objects.get_or_create(
            title="Поради для першого місяця інтернатури",
            defaults={
                "author": intern,
                "content": "Ведіть щоденник кейсів, ставте питання наставнику і повторюйте протоколи щодня.",
                "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            },
        )[0]
        InternshipPost.objects.get_or_create(
            title="Список корисних вебінарів",
            defaults={
                "author": teacher,
                "content": "Добірка відкритих вебінарів з терапії, ортопедії та комунікації з пацієнтом.",
            },
        )
        InternshipVote.objects.update_or_create(post=internship_post, user=teacher, defaults={"vote_type": InternshipVote.PLUS})
        InternshipVote.objects.update_or_create(post=internship_post, user=student, defaults={"vote_type": InternshipVote.PLUS})

        UserPost.objects.get_or_create(
            title="Як я готуюся до тестів Dentoria",
            defaults={
                "author": student,
                "content": "Спочатку проходжу матеріали, потім виписую терміни і тільки після цього складаю тест.",
                "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            },
        )
        UserPost.objects.get_or_create(
            title="Добірка джерел для інтернів",
            defaults={
                "author": teacher,
                "content": "Рекомендую почати з протоколів ізоляції, діагностики та планування лікування.",
            },
        )

        CalendarEvent.objects.get_or_create(
            title="Публічний вебінар: сучасна ендодонтія",
            starts_at=timezone.now() + timezone.timedelta(days=2),
            defaults={
                "author": teacher,
                "description": "Відкрита подія для всіх користувачів Dentoria.",
                "event_type": "webinar",
                "external_url": "https://example.com/webinar",
                "ends_at": timezone.now() + timezone.timedelta(days=2, hours=2),
                "is_public": True,
            },
        )
        CalendarEvent.objects.get_or_create(
            title="Приватне нагадування: повторити тест",
            starts_at=timezone.now() + timezone.timedelta(days=1),
            defaults={
                "author": student,
                "description": "Особиста подія студента.",
                "event_type": "personal",
                "ends_at": timezone.now() + timezone.timedelta(days=1, hours=1),
                "is_public": False,
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data created."))
        self.stdout.write("Users:")
        self.stdout.write(f"  admin_demo / {demo_password}")
        self.stdout.write(f"  teacher_demo / {demo_password}")
        self.stdout.write(f"  student_demo / {demo_password}")
        self.stdout.write(f"  intern_demo / {demo_password}")

    def _user(self, username, email, password, **flags):
        user, created = User.objects.get_or_create(username=username, defaults={"email": email, **flags})
        if created:
            user.set_password(password)
            user.is_active = True
            for field, value in flags.items():
                setattr(user, field, value)
            user.save()
        return user

    def _course(self, author, title, description, status, cover_image_url=""):
        course, _ = Course.objects.get_or_create(
            title=title,
            author=author,
            defaults={"description": description, "status": status, "cover_image_url": cover_image_url},
        )
        if course.status != status:
            course.status = status
            course.save()
        return course

    def _material(self, **kwargs):
        material, _ = CourseMaterial.objects.get_or_create(
            course=kwargs["course"],
            title=kwargs["title"],
            defaults=kwargs,
        )
        return material

    def _test(self, course, title, description, passing_score):
        test, _ = Test.objects.get_or_create(
            course=course,
            title=title,
            defaults={"description": description, "passing_score": passing_score},
        )
        return test

    def _question(self, test, text, order):
        question, _ = Question.objects.get_or_create(test=test, text=text, defaults={"order": order})
        return question

    def _answer(self, question, text, is_correct):
        answer, _ = AnswerOption.objects.get_or_create(question=question, text=text, defaults={"is_correct": is_correct})
        return answer
