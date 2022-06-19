# Tests for models
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from core import models


def create_user(email='user@example.com', password='secret'):
    """helper function to create a new user for testing"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    # Test for models

    def test_create_user_with_email_successful(self):
        # Test for create user with given email and passwd
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))  # password is hashed

    def test_user_email_normalized(self):
        # test for user email normalization
        # part before @ keeps capitalization, part after should be lower case
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com']
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'secret')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        # new user should have an email address
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'secret')

    def test_create_superuser(self):
        # Test for creation of superuser
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'secret'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        # Test: creating recipe successfully
        # recipe: user as Foreign Key
        # Test if creation is successful
        user = get_user_model().objects.create_user(
            email='test@example.com',
            password='secret'
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample 1 recipe',
            price=Decimal('5.50'),
            description='Sample recipe for testing'
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """
        Test creating a tag
        """
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='testTag1')

        self.assertEqual(str(tag), tag.name)
