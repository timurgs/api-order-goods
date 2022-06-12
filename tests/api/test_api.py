import pytest
from django.urls import reverse
from rest_framework.authtoken.models import Token

from backend.models import User, ConfirmEmailToken, ResetPasswordToken


@pytest.mark.django_db
def test_register_view(api_client):
    register_data = {
        'last_name': 'Ivanov',
        'first_name': 'Ivan',
        'middle_name': 'Ivanovich',
        'email': 'ivanov@ivan.ru',
        'password': 'sgdsSTAT4434FET323256',
        'company': 'IvanovCompany',
        'position': 'Manager'
    }
    url = reverse('backend:register')
    response = api_client.post(url, register_data)
    assert response.status_code == 200
    assert response.json()['Status'] is True


@pytest.mark.django_db
def test_confirm_view(api_client):
    user = User.objects.create_user(
        last_name='Ivanov',
        first_name='Ivan',
        middle_name='Ivanovich',
        email='ivanov@ivan.ru',
        password='sgdsSTAT4434FET323256',
        company='IvanovCompany',
        position='Manager'
    )
    token = ConfirmEmailToken.objects.create(user_id=user.id)
    input_data = {'email': 'ivanov@ivan.ru', 'token': token.key}
    url = reverse('backend:confirm')
    response = api_client.post(url, input_data)
    assert response.status_code == 200
    assert response.json()['Status'] is True


@pytest.mark.django_db
def test_account_data_list(api_client):
    url = reverse('backend:account-data')
    user = User.objects.create_user(
        last_name='Ivanov',
        first_name='Ivan',
        middle_name='Ivanovich',
        email='ivanov@ivan.ru',
        password='sgdsSTAT4434FET323256',
        company='IvanovCompany',
        position='Manager',
        is_active=True
    )
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()['id'] == user.id


@pytest.mark.django_db
def test_account_data_update(api_client):
    updated_data = {'first_name': 'Ivan1'}
    url = reverse('backend:account-data')
    user = User.objects.create_user(
        last_name='Ivanov',
        first_name='Ivan',
        middle_name='Ivanovich',
        email='ivanov@ivan.ru',
        password='sgdsSTAT4434FET323256',
        company='IvanovCompany',
        position='Manager',
        is_active=True
    )
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    response = api_client.put(url, updated_data)
    assert response.status_code == 200
    assert response.json()['Status'] is True


@pytest.mark.django_db
def test_reset_password_request_token_view(api_client):
    url = reverse('backend:reset-password-token')
    User.objects.create_user(
        last_name='Ivanov',
        first_name='Ivan',
        middle_name='Ivanovich',
        email='ivanov@ivan.ru',
        password='sgdsSTAT4434FET323256',
        company='IvanovCompany',
        position='Manager',
        is_active=True
    )
    input_data = {'email': 'ivanov@ivan.ru'}
    response = api_client.post(url, input_data)
    assert response.status_code == 200
    assert response.json()['Status'] is True


@pytest.mark.django_db
def test_reset_password_view(api_client):
    user = User.objects.create_user(
        last_name='Ivanov',
        first_name='Ivan',
        middle_name='Ivanovich',
        email='ivanov@ivan.ru',
        password='sgdsSTAT4434FET323256',
        company='IvanovCompany',
        position='Manager',
        is_active=True
    )
    token = ResetPasswordToken.objects.create(user_id=user.id)
    input_data = {'email': 'ivanov@ivan.ru', 'token': token.key, 'new_password': 'sgdsSTAT4434FET1'}
    url = reverse('backend:reset-password')
    response = api_client.post(url, input_data)
    assert response.status_code == 200
    assert response.json()['Status'] is True
