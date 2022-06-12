from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from celery import shared_task

from backend.models import ConfirmEmailToken, User, ResetPasswordToken


@shared_task
def password_reset_token_created(user_id):
    """
    Отправляем письмо с токеном для сброса пароля
    """
    token, _ = ResetPasswordToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title
        f'Password Reset Token for {token.user}',
        # message
        token.key,
        # from
        settings.EMAIL_HOST_USER,
        # to
        [token.user.email]
    )
    msg.send()


@shared_task
def new_user_registered(user_id):
    """
    отправляем письмо с подтрердждением почты
    """
    # print(user_id)
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title
        f'Confirmation Email Token for {token.user}',
        # message
        token.key,
        # from
        settings.EMAIL_HOST_USER,
        # to
        [token.user.email]
    )
    msg.send()


@shared_task
def new_order_user(user_id):
    """
    отправляем письмо при изменении статуса заказа пользователю
    """
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # title
        'Обновление статуса заказа',
        # message
        'Заказ сформирован',
        # from
        settings.EMAIL_HOST_USER,
        # to
        [user.email]
    )
    msg.send()


@shared_task
def new_order_admin(user_id):
    """
    отправляем письмо для исполнения заказа поставщику
    """
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # title
        'Исполнение заказа',
        # message
        'Заказ подтвержден',
        # from
        settings.EMAIL_HOST_USER,
        # to
        [user.email]
    )
    msg.send()
