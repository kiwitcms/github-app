# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors

from django.conf import settings

from tcms_tenants.tests import LoggedInTestCase

from tcms_github_app import menu


class DiscoveredAsPluginTestCase(LoggedInTestCase):
    def test_menu_is_updated(self):
        """
            Given there are some plugins installed
            Then navigation menu under PLUGINS will be extended
        """
        for name, target in settings.MENU_ITEMS:
            if name == 'PLUGINS':
                for menu_item in menu.MENU_ITEMS:
                    self.assertIn(menu_item, target)

                return

        self.fail('PLUGINS not found in settings.MENU_ITEMS')

    def test_menu_rendering(self):
        """
            Given there are some plugins installed
            Then navigation menu under PLUGINS will be rendered.
        """
        response = self.client.get('/')
        self.assertContains(
            response,
            "<a class='dropdown-toggle' href='#' data-toggle='dropdown'>GitHub integration</a>",
            html=True)
        self.assertContains(response,
                            '<a href="/kiwitcms_github_app/appedit/" target="_parent">Settings</a>',
                            html=True)
