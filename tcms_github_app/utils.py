# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from tcms.management.models import Classification
from tcms.management.models import Product


def create_product_from_repository(data):
    name = data.payload['repository']['full_name']
    description = data.payload['repository']['description']
    classification, _ = Classification.objects.get_or_create(name='Imported from GitHub')

    if not Product.objects.filter(name=name).exists():
        Product.objects.create(
            name=name,
            description=description,
            classification=classification,
        )
