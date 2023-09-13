import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Choice, Question


class TestModels(TestCase):

    def test_question_and_choice(self):
        self.assertEqual(len(Question.objects.all()), 0)
        q = Question(question_text="What's new?", pub_date=timezone.now())
        q.save()
        self.assertEqual(len(Question.objects.all()), 1)
        self.assertEqual(q.question_text, "What's new?")
        self.assertTrue(Question.objects.get(pub_date__year=timezone.now().
                                             year).was_published_recently())
        q.choice_set.create(choice_text='Not much', votes=0)
        q.choice_set.create(choice_text='The sky', votes=0)
        self.assertEqual(len(q.choice_set.all()), 2)
        self.assertEqual(q.choice_set.count(), 2)
        c = q.choice_set.create(choice_text='Just hacking again', votes=0)
        self.assertEqual(c.question, q)
        c = q.choice_set.filter(choice_text__startswith='Just hacking')
        self.assertEqual(len(c), 1)
        self.assertEqual(len(Choice.objects.all()), 3)
        c.delete()
        self.assertEqual(len(c), 0)
        self.assertEqual(len(Choice.objects.all()), 2)

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59,
                                                   seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


class TestViews(TestCase):

    def test_404(self):
        response = self.client.get('/nonexist')
        self.assertEqual(response.status_code, 404)

    def test_main(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_polls(self):
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)

    def test_polls0(self):
        response = self.client.get(reverse('polls:detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 404)
        create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        create_question(question_text="Past question 1.", days=-30)
        create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 2.>', '<Question: Past question 1.>']
        )
