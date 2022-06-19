# Test for recipe APIs
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Recipe

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    # create and return a recipe detail URL based on the requested id
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_user(**params):
    # create new user for testing
    return get_user_model().objects.create_user(**params)

def create_recipe(user, **params):
    # create and return a sample recipe
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('1.19'),
        'description': 'Sample recipe description',
        'link': 'http://example.com/SampleRecipe.txt'
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


class PublicRecipeAPITests(TestCase):
    # Test APIs for unauthenticated users
    # return should be code 401 

    def setUp(self):
        # setup client
        self.client = APIClient()

    def test_auth_required(self):
        # test authentication
        # return should be 401 unauthorized
        res = self.client.get(RECIPE_URL)
        
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    # Test APIs for auth user

    def setUp(self):
        # setup client and user and force authenticate user
        self.client = APIClient()
        self.user = create_user(email='testuser@example.com', password='secret')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        # Test retrieving recipe list
        # Test: create several recipes
        # Test: retrieve these recipes
        # Test: retrieving should return 200 and correct items
        for _ in range(5):
            create_recipe(self.user)
        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        # test if recipe list returned by API belongs to current user
        # tests: make a different user
        #        create a list of recipes for default user
        #        create a list of recipes for different user
        #        query recipes with key = self.user
        #        API returned recipes should == recipes belong to default user
        dif_user = create_user(email='diffuser@example.com', password='secret')
        create_recipe(self.user)
        create_recipe(dif_user)

        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)
    
    def test_get_recipe_detail(self):
        # Test get recipe detail API
        # 1. create a recipe and get it's uls
        # 2. API call to get this recipe
        # 3. response should == created recipe
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        # test creating recipe
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('6.50')
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(recipe.user, self.user)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

    def test_partial_update(self):
        # update recipe partially tests
        original_link = 'http://example.com/recipe'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link,
        )

        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        # test for full update recipe: request method = put        
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='http://example.com/recipe',
            description='Sample recipe description'
        )

        payload = {
            'title': 'New recipe title',
            'link': 'http://new.com/recipe',
            'description': 'New recipe description',
            'price': Decimal('1.99'),
            'time_minutes': 21,
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)
    
    def test_update_user_returns_error(self):
        # update of user should be forbidden
        new_user = create_user(email='user2@example.com', password='secret')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        # Test deleting recipe successfully
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_error(self):
        # Test deleting other user's recipe is forbidden
        other_user = create_user(email='user2@example.com', password='secret')
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
