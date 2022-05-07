from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created

from backend.models import ConfirmEmailToken, User


new_user_registered = Signal()

new_order_user = Signal()

new_order_admin = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    Отправляем письмо с токеном для сброса пароля
    """

    msg = EmailMultiAlternatives(
        # title
        f'Password Reset Token for {reset_password_token.user}',
        # message
        reset_password_token.key,
        # from
        settings.EMAIL_HOST_USER,
        # to
        [reset_password_token.user.email]
    )
    msg.send()


@receiver(new_user_registered)
def new_user_registered_send_message(user_id, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """
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


@receiver(new_order_user)
def new_order_send_message_user(user_id, **kwargs):
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


@receiver(new_order_admin)
def new_order_send_message_admin(user_id, **kwargs):
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
