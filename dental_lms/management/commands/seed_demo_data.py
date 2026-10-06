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
    help = "Create modern Dentoria demo content for local manual testing."

    def handle(self, *args, **options):
        demo_password = "DemoPass123"
        editorial = self._user("dentoria_editor", "editor@dentoria.test", demo_password, is_staff=True)
        student = self._user("student_demo", "student@dentoria.test", demo_password)
        admin = self._user("admin_demo", "admin@dentoria.test", demo_password, is_staff=True, is_superuser=True)

        demo_users = User.objects.filter(username__in=["dentoria_editor", "student_demo", "admin_demo", "teacher_demo", "intern_demo"])
        self._clear_demo_content(demo_users)

        editorial.first_name = "Dentoria"
        editorial.last_name = "Editorial"
        editorial.save()
        editorial.profile.specialization = "Редакція стоматологічної освіти"
        editorial.profile.bio = "Єдиний редакційний акаунт для демо-постів, вакансій і подій Dentoria."
        editorial.profile.avatar_url = "/static/img/dentoria-post.svg"
        editorial.profile.theme = "orange"
        editorial.profile.save()

        student.profile.specialization = "Студент стоматології"
        student.profile.bio = "Тестовий студент для перевірки прогресу, тем і проходження курсів."
        student.profile.theme = "light"
        student.profile.save()

        courses = [
            self._course(
                editorial,
                "AI у стоматологічній діагностиці",
                "Як безпечно використовувати ШІ для аналізу знімків, документації та клінічного triage без заміни лікарського рішення.",
                Course.PUBLISHED,
                "/static/img/dentoria-ai-diagnostics.svg",
            ),
            self._course(
                editorial,
                "Профілактика карієсу та пародонтальних захворювань",
                "Сучасний профілактичний підхід: оцінка ризиків, мотивація пацієнта, фториди, контроль біоплівки та recall-система.",
                Course.PUBLISHED,
                "/static/img/dentoria-prevention.svg",
            ),
            self._course(
                editorial,
                "Цифровий протокол ендодонтії",
                "Практичний курс про діагностику, ізоляцію, робочу довжину, інструментацію, іригацію та якісну обтурацію.",
                Course.PUBLISHED,
                "/static/img/dentoria-endo.svg",
            ),
            self._course(
                editorial,
                "Чернетка: телестоматологія в клініці",
                "Матеріали ще готуються. Курс демонструє режим чернетки та поступове наповнення.",
                Course.DRAFT,
                "",
            ),
        ]

        for index, course in enumerate(courses, start=1):
            self._material(course, "Клінічний конспект", "text", index, text_content=f"Ключові принципи теми: {course.title}. Додайте нотатки, клінічні приклади та алгоритми прийняття рішень.")
            self._material(course, "Додатковий матеріал", "link", index + 10, external_url="https://www.who.int/health-topics/oral-health")
            if course.status == Course.PUBLISHED:
                self._material(course, "Ілюстрація протоколу", "image", index + 20, image_url=course.cover_image_url or "/static/img/dentoria-post.svg")
                test = self._test(course, f"Тест: {course.title}", "Швидка перевірка розуміння матеріалу.", 60)
                question = self._question(test, "Який підхід найкраще відповідає сучасній доказовій стоматології?", 1)
                self._answer(question, "Оцінка ризиків, документація та персоналізований план", True)
                self._answer(question, "Однаковий план лікування для всіх пацієнтів", False)

        main_course = courses[0]
        enrollment, _ = CourseEnrollment.objects.get_or_create(user=student, course=main_course)
        completed = main_course.materials.first()
        if completed:
            MaterialProgress.objects.update_or_create(
                user=student,
                material=completed,
                defaults={"is_completed": True, "completed_at": timezone.now()},
            )
        enrollment.progress = 33
        enrollment.save()
        first_test = main_course.tests.first()
        if first_test:
            TestAttempt.objects.get_or_create(user=student, test=first_test, defaults={"score": 82, "max_score": 100, "passed": True})

        for job in [
            {
                "title": "Асистент стоматолога у цифрову клініку",
                "clinic_name": "Dentoria Digital Clinic",
                "city": "Київ",
                "short_description": "Роль для спеціаліста, який хоче працювати з цифровими протоколами, скануванням і сучасною комунікацією з пацієнтом.",
                "requirements": "Уважність, базові знання асептики, готовність навчатися intraoral scanning workflow.",
                "responsibilities": "Підготовка кабінету, асистування, стерилізація, допомога з цифровою документацією.",
            },
            {
                "title": "Лікар-інтерн з фокусом на профілактику",
                "clinic_name": "Orange Dental Hub",
                "city": "Львів",
                "short_description": "Інтернатура з наставником, щотижневими розборами кейсів і профілактичними протоколами.",
                "requirements": "Медична освіта, комунікабельність, бажання працювати за доказовими протоколами.",
                "responsibilities": "Участь у прийомах, ведення історій, мотиваційні бесіди з пацієнтами.",
            },
            {
                "title": "Координатор освітніх вебінарів Dentoria",
                "clinic_name": "Dentoria Academy",
                "city": "Remote",
                "short_description": "Підготовка вебінарів, календаря подій і навчальних матеріалів для стоматологічної спільноти.",
                "requirements": "Організованість, грамотна українська, базове розуміння стоматологічних тем.",
                "responsibilities": "Публікація подій, комунікація зі спікерами, оновлення матеріалів LMS.",
            },
        ]:
            JobVacancy.objects.create(
                author=editorial,
                full_description=f"{job['short_description']} Позиція створена для демонстрації фільтрів вакансій у Dentoria.",
                conditions="Гнучкий графік, наставництво, прозорі задачі, розвиток у команді.",
                contact_info="careers@dentoria.test",
                is_active=True,
                **job,
            )

        internship_posts = [
            ("Як інтерну працювати з AI-підказками без клінічних помилок", "ШІ може допомогти структурувати документацію або знайти пропущені деталі, але остаточне рішення завжди має залишатися за лікарем і наставником."),
            ("Чекліст першого прийому: що фіксувати в історії", "Скарга, анамнез, фото, рентген-дані, пародонтальний статус, ризики карієсу та узгоджений план — мінімальна база якісної документації."),
            ("Телестоматологія: коли онлайн-консультація доречна", "Попередній triage, контроль після втручання та навчання гігієні можуть працювати онлайн, але діагноз і лікування часто потребують очного огляду."),
        ]
        for index, (title, content) in enumerate(internship_posts):
            post = InternshipPost.objects.create(author=editorial, title=title, content=content, image_url="/static/img/dentoria-post.svg")
            InternshipVote.objects.update_or_create(post=post, user=student, defaults={"vote_type": InternshipVote.PLUS})

        user_posts = [
            ("AI в стоматології: що варто тестувати вже зараз", "Найбільш практичні сценарії для клініки: попередня розмітка знімків, пошук ризиків у документації, підготовка patient-friendly пояснень і контроль follow-up."),
            ("Профілактика як головна стратегія 2026", "Фокус зміщується від реактивного лікування до ризик-орієнтованого супроводу: recall, контроль біоплівки, фториди, харчові звички та мотиваційне інтервʼю."),
            ("Цифровий шлях пацієнта в стоматології", "Онлайн-запис, зрозумілі нагадування, цифрові знімки, фото-протоколи та прозорий план лікування підвищують довіру пацієнтів."),
            ("Оральне здоровʼя і системні захворювання", "Стоматологічна команда має враховувати загальний стан пацієнта, медикаменти, метаболічні ризики та звʼязок із хронічними станами."),
        ]
        for index, (title, content) in enumerate(user_posts):
            UserPost.objects.create(
                author=editorial,
                title=title,
                content=content,
                image_url="/static/img/dentoria-post.svg",
            )

        now = timezone.now()
        events = [
            ("Вебінар: AI-рішення в dental imaging", "webinar", "Порівняємо сценарії використання ШІ у 2D-знімках, документації та комунікації з пацієнтом.", 2, True),
            ("Практикум: профілактичний план для пацієнта з високим caries risk", "webinar", "Ризик-орієнтований recall, домашній догляд і контроль результатів.", 5, True),
            ("Курс Dentoria: цифровий протокол ендодонтії", "internal_course", "Подія привʼязана до внутрішнього курсу LMS.", 7, True),
            ("Редакційне планування контенту", "personal", "Приватна службова подія редакції Dentoria.", 1, False),
        ]
        for title, event_type, description, days, is_public in events:
            CalendarEvent.objects.create(
                author=editorial,
                title=title,
                description=description,
                event_type=event_type,
                external_url="https://example.com/dentoria-event" if event_type == "webinar" else "",
                related_course=courses[2] if event_type == "internal_course" else None,
                starts_at=now + timezone.timedelta(days=days),
                ends_at=now + timezone.timedelta(days=days, hours=2),
                is_public=is_public,
            )

        self.stdout.write(self.style.SUCCESS("Modern demo data created."))
        self.stdout.write("Users:")
        self.stdout.write(f"  dentoria_editor / {demo_password}")
        self.stdout.write(f"  student_demo / {demo_password}")
        self.stdout.write(f"  admin_demo / {demo_password}")

    def _clear_demo_content(self, demo_users):
        Course.objects.filter(author__in=demo_users).delete()
        JobVacancy.objects.filter(author__in=demo_users).delete()
        InternshipPost.objects.filter(author__in=demo_users).delete()
        UserPost.objects.filter(author__in=demo_users).delete()
        CalendarEvent.objects.filter(author__in=demo_users).delete()

    def _user(self, username, email, password, **flags):
        user, created = User.objects.get_or_create(username=username, defaults={"email": email, **flags})
        user.email = email
        user.is_active = True
        for field, value in flags.items():
            setattr(user, field, value)
        user.set_password(password)
        user.save()
        return user

    def _course(self, author, title, description, status, cover_image_url=""):
        course = Course.objects.create(author=author, title=title, description=description, status=status, cover_image_url=cover_image_url)
        return course

    def _material(self, course, title, material_type, order, **fields):
        return CourseMaterial.objects.create(course=course, title=title, material_type=material_type, order=order, **fields)

    def _test(self, course, title, description, passing_score):
        return Test.objects.create(course=course, title=title, description=description, passing_score=passing_score)

    def _question(self, test, text, order):
        return Question.objects.create(test=test, text=text, order=order)

    def _answer(self, question, text, is_correct):
        return AnswerOption.objects.create(question=question, text=text, is_correct=is_correct)
