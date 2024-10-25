from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.email = 'testuser@example.com'
        self.password = 'TestPass123'
        self.user = self.User.objects.create_user(email=self.email, password=self.password)

    # def setUp(self):
    #     self.email = 'test@example.com'
    #     self.password = 'Testpass123'
    #     self.user = User.objects.create_user(
    #         email=self.email,
    #         password=self.password
    #     )

    # def get_token(self):
    #     refresh = RefreshToken.for_user(self.user)
    #     return str(refresh.access_token)

    def get_token(self):
        url = reverse("users:token_obtain_pair")
        data = {
            'email': self.email,
            'password': self.password
        }
        response = self.client.post(url, data)
        print(response.data)
        return response.data.get('access')  # Повертає токен доступу

    def test_create_user(self):
        """Test creating a new user"""
        url = reverse('users:create')
        data = {
            'email': 'newuser@example.com',
            'password': 'NewPass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertIn('email', response.data)
        self.assertNotIn('password', response.data)

    def test_login_user(self):
        """Тест логіну користувача та отримання токена"""
        url = reverse("users:token_obtain_pair")
        data = {
            'email': self.email,
            'password': self.password
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_retrieve_user_profile(self):
        """Тест отримання профілю користувача після авторизації"""
        url = reverse("users:manage")
        token = self.get_token()  # Переконайтеся, що це дійсний токен
        print(f"Using Token: {token}")  # Вивести токен
        self.client.credentials(HTTP_AUTHORIZE=f'Bearer {token}')
        response = self.client.get(url)
        print(response.data)  # Вивести відповідь для діагностики
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.email)

    def test_update_user_profile(self):
        """Тест оновлення профілю користувача"""
        url = reverse("users:manage")
        token = self.get_token()  # Переконайтеся, що це дійсний токен
        self.client.credentials(HTTP_AUTHORIZE=f'Bearer {token}')

        # Дані для оновлення
        data = {
            'email': 'updatedemail@example.com',
            'password': 'NewPassword123'
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Перевірте, що дані оновлено в базі даних
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.email, 'updatedemail@example.com')

        # Перевірте, що пароль оновлений
        self.user.refresh_from_db()  # Оновлення екземпляра з бази даних
        self.user.set_password('NewPassword123')  # Задайте новий пароль
        self.user.save()  # Збережіть зміни

        # Перевірте, що новий пароль працює
        self.assertTrue(self.user.check_password('NewPassword123'))



