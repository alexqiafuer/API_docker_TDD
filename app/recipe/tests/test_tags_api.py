"""
Tests for Tags APIs
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """create and return a tag detail url"""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example', password='secret'):
    """Create user for testing"""
    return get_user_model().objects.create_user(email, password)


class PublicTagsAPITests(TestCase):
    """Test for unauthenticated APT requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for accessing tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Tests for retrieving tags"""
        tag_names = ['Vegan', 'Dessert', 'Soup', 'Hot', 'Cold', 'Entree']
        for name in tag_names:
            Tag.objects.create(user=self.user, name=name)
        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user"""
        user2 = create_user(email='user2@example.com')
        Tag.objects.create(user=user2, name='Pretty')
        tag = Tag.objects.create(user=self.user, name='Ugly')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test updating a tag"""
        tag = Tag.objects.create(user=self.user, name='Test tag')
        payload = {'name': 'Update test tag'}
        tag_url = detail_url(tag.id)
        res = self.client.patch(tag_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting a tag"""
        tag = Tag.objects.create(user=self.user, name='Delete tag')

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_tags_assigned_to_recipes(self):
        """Test listing tags that were assigned to recipes only"""
        tag1 = Tag.objects.create(user=self.user, name='Apple')
        tag2 = Tag.objects.create(user=self.user, name='Pear')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Sample recipe',
            time_minutes=20,
            price=Decimal('11.45'),
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered tags return unique"""
        tag = Tag.objects.create(user=self.user, name='Apple')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Sample recipe1',
            time_minutes=21,
            price=Decimal('11.45'),
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Sample recipe2',
            time_minutes=22,
            price=Decimal('12.45'),
        )
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
        # serializer = TagSerializer(tag, many=False)
        # self.assertEqual(res.data, serializer.data)
