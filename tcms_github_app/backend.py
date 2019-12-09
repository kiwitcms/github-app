from social_core.backends.github import GithubOAuth2
from social_core.utils import handle_http_errors


# Remove once shipped in social-auth-core, see
# https://github.com/python-social-auth/social-core/pull/413/
class GithubAppAuth(GithubOAuth2):  # pylint: disable=abstract-method
    """GitHub App OAuth authentication backend"""
    name = 'github-app'

    def validate_state(self):
        """
            Scenario 1: user clicks an icon/button on your website and
                initiates social login. This works exacltly like standard
                OAuth and we have `state` and `redirect_uri`.
            Scenario 2: user starts from http://github.com/apps/your-app
                and clicks 'Install & Authorize' button! They still get
                a temporary `code` (used to fetch `access_token`) but
                there's no `state` or `redirect_uri` here.
            Note: Scenario 2 only happens when your GitHub App is configured
                with `Request user authorization (OAuth) during installation`
                turned on! This causes GitHub to redirect the person back to
                `/complete/github/`. If the above setting is turned off then
                GitHub will redirect to another URL called Setup URL and the
                person may need to login first before they can continue!
        """
        if self.data.get('installation_id') and self.data.get('setup_action'):
            return None

        return super().validate_state()

    # when Installing after OAuth and while being logged into Kiwi TCMS
    # the session cookie persists and collides with a new cookies/new access_token
    # so automatic login isn't performed. When clicking the login button everything
    # works though. I still don't know what happens exactly
    @handle_http_errors
    def do_auth(self, access_token, *args, **kwargs):
        # kwargs['user'] = None
        # self.strategy.session.delete()
        return super().do_auth(access_token, *args, **kwargs)
