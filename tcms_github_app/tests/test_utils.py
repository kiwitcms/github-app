# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import json
from datetime import datetime

from django.test import TestCase

from tcms_github_marketplace import utils


class CalculatePaidUntilTestCase(TestCase):
    def test_monthly_cycle(self):
        mp_purchase = json.loads("""
{
  "account":{
     "type":"Organization",
     "id":18404719,
     "login":"username",
     "organization_billing_email":"username@email.com"
  },
  "billing_cycle":"monthly",
  "unit_count":1,
  "on_free_trial":false,
  "free_trial_ends_on":null,
  "next_billing_date":null,
  "plan":{
     "id":435,
     "name":"Public Tenant",
     "description":"Basic Plan",
     "monthly_price_in_cents":3200,
     "yearly_price_in_cents":32000,
     "price_model":"flat",
     "has_free_trial":false,
     "unit_name":"seat",
     "bullets":[
        "Is Basic",
        "Because Basic "
     ]
  }
}
""".strip())
        effective_date = datetime(2019, 4, 1, 0, 0, 0, 0)
        paid_until = utils.calculate_paid_until(mp_purchase, effective_date)
        expected = datetime(2019, 5, 2, 23, 59, 59, 0)  # 31 days

        self.assertEqual(paid_until, expected)

    def test_yearly_cycle(self):
        mp_purchase = json.loads("""
{
  "account":{
     "type":"Organization",
     "id":18404719,
     "login":"username",
     "organization_billing_email":"username@email.com"
  },
  "billing_cycle":"yearly",
  "unit_count":1,
  "on_free_trial":false,
  "free_trial_ends_on":null,
  "next_billing_date":null,
  "plan":{
     "id":435,
     "name":"Public Tenant",
     "description":"Basic Plan",
     "monthly_price_in_cents":3200,
     "yearly_price_in_cents":32000,
     "price_model":"flat",
     "has_free_trial":false,
     "unit_name":"seat",
     "bullets":[
        "Is Basic",
        "Because Basic "
     ]
  }
}
""".strip())
        effective_date = datetime(2019, 4, 1, 0, 0, 0, 0)
        paid_until = utils.calculate_paid_until(mp_purchase, effective_date)
        expected = datetime(2020, 4, 1, 23, 59, 59, 0)  # 366 days

        self.assertEqual(paid_until, expected)
