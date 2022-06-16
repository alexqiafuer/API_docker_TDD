# Tests for user API
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

TEST_PAY_LOAD = {
    'email': 'test@example.com',
    'password': 'secret',
    'name': 'Test name',
}


def create_user(**params):
    # create a new user, return user object
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    # Tests public user APIs, registration for new user
    # creation should return 201 upon success
    # created user should be based on the provided information
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        # Test for: create user successfully
        res = self.client.post(CREATE_USER_URL, TEST_PAY_LOAD)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=TEST_PAY_LOAD['email'])
        self.assertTrue(user.check_password(TEST_PAY_LOAD['password']))
        self.assertNotIn('password', res.data)  # password should be hashed

    def test_user_with_email_exists_error(self):
        # test for the case: user to be created already exists
        # client should return code 400 bad request
        create_user(**TEST_PAY_LOAD)
        res = self.client.post(CREATE_USER_URL, TEST_PAY_LOAD)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        # test for: password too short error(< 5 chars)
        # client should return code 400
        # user should not exists in db
        test_pay_load = TEST_PAY_LOAD.copy()
        test_pay_load['password'] = 'pwd'
        res = self.client.post(CREATE_USER_URL, test_pay_load)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=test_pay_load['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        # Test token generation for users
        # Assume user existing in db
        # tests: 1. token is generated and included in 'POST' response,
        #        2. status code 200 OK is returned
        create_user(**TEST_PAY_LOAD)
        pay_load = {
            'email': TEST_PAY_LOAD['email'],
            'password': TEST_PAY_LOAD['password']
        }
        res = self.client.post(TOKEN_URL, pay_load)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credential(self):
        # Test for return error is credential is bad
        create_user(**TEST_PAY_LOAD)
        payload = {
            'email': TEST_PAY_LOAD['email'],
            'password': 'somethingelse',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        # test for return error if password is blank
        create_user(**TEST_PAY_LOAD)
        payload = {
            'email': TEST_PAY_LOAD['email'],
            'password': '',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        #  test authentication is required for users
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    # Test api that requires authentication

    def setUp(self):
        self.user = create_user(**TEST_PAY_LOAD)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        # test retrieving profile for logged in user
        # test: return code 200
        # test: data content correct
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        # test if 'POST' method is disabled or not
        res = self.client.post(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        # test updating the user profile for authenticated user
        pay_load = {
            'name': 'updatedname',
            'password': 'updatedpwd',
        }

        res = self.client.patch(ME_URL, pay_load)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, pay_load['name'])
        self.assertTrue(self.user.check_password(pay_load['password']))
