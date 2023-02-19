from django.db import models
from django.utils import timezone


class Client(models.Model):
    name = models.CharField('name', max_length=50)
    telegram_id = models.CharField('telegram id', max_length=50)
    registration_date = models.DateTimeField('date of registration', auto_now=True,)
    subscription_end = models.DateTimeField('end of subscription date')

    @property
    def is_active(self):
        if timezone.now() < self.subscription_end:
            return True
        else:
            return False
    
    def __str__(self):
        return self.name


class Subcontractor(models.Model):

    STATUS_CHOICES = [
        ('on_check', 'На одобрении'),
        ('enable', 'Подтвержден'),
        ('disable', 'Заблокирован'),
    ]
    name = models.CharField('name', max_length=50)
    telegram_id = models.CharField('telegram id', max_length=50)
    chat_id = models.CharField('chat id', max_length=50)
    registration_date = models.DateTimeField('date of registration', auto_now=True,)
    salary = models.IntegerField('salary', blank=True, null=True)
    is_active = models.BooleanField('is active', default=False)
    on_check = models.BooleanField('on_check', default=False)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES[2],
    )

    def __str__(self):
        return self.name


class Request(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='client', related_name='requests')
    subcontractor = models.ForeignKey(Subcontractor, verbose_name='subcontractor', on_delete=models.SET_NULL, related_name='requests', blank=True, null=True)
    creation_date = models.DateTimeField('request creation date', auto_now=True)
    title = models.CharField('title', max_length=50)
    description = models.TextField('description')
    price = models.IntegerField('price', blank=True, null=True)
    estimate = models.DateTimeField('estimate', blank=True, null=True)
    php_login = models.CharField('php login', max_length=50, blank=True, null=True)
    php_password = models.CharField('php password', max_length=50, blank=True, null=True)
    php_link = models.CharField('php link', max_length=50, blank=True, null=True)

    REQUEST_STATUS_CHOICES = [
         ('pending', 'Pending'),
         ('open', 'Open'),
         ('working', 'In work'),
         ('complete', 'Complete'),
         ('cancelled', 'Cancelled'),
    ]

    status = models.CharField(
        max_length=10,
        choices=REQUEST_STATUS_CHOICES,
        default=REQUEST_STATUS_CHOICES[0],
    )

    REQUEST_DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    difficulty = models.CharField(
        max_length=10,
        choices=REQUEST_DIFFICULTY_CHOICES,
        default=REQUEST_DIFFICULTY_CHOICES[1]
    )

    def __str__(self):
        return self.title


class Clarification(models.Model):
    question = models.TextField('question')
    answer = models.TextField('answer')
    creation_date = models.DateTimeField('request creation date', auto_now=True)
    request = models.ForeignKey(Request, verbose_name='request', on_delete=models.CASCADE, related_name='clarifications')

    def __str__(self):
        return self.question
