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
        self.user = get_user_model().objects.create_user(
            'testuser@example.com', 'secret'
        )
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
        dif_user = get_user_model().objects.create_user(
            'diffuser@example.com', 'secret'
        )
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
        url = detail_url(recipe)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = RecipeSerializer(recipe)
        self.assertEqual(res.data, serializer.data)