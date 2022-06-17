# Test for recipe APIs
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import APIClient
from rest_framework import status

from core.models import Recipe