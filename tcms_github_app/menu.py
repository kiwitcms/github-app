# Copyright (c) 2019-2020 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


# Follows the format of ``tcms.settings.common.MENU_ITEMS``
MENU_ITEMS = [
    (_('GitHub integration'), [
        (_('Resync'), reverse_lazy('github_app_resync')),
        (_('Settings'), reverse_lazy('github_app_edit')),
    ]),
]
