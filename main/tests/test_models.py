from decimal import Decimal
from django.test import TestCase
from main import models


class TestModel(TestCase):
    def test_active_manager_works(self):
        models.Product.objects.create(
            name="The cathedral and the bazaar",
            price=Decimal("20.00"))
        models.Product.objects.create(
            name="Pride and Prejudice",
            price=Decimal("2.00"))
        models.Product.objects.create(
            name="A tale of two cities",
            price=Decimal("2.00"),
            active=False)
        self.assertEqual(len(models.Product.objects.active()), 2)
