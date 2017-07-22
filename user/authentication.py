from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model, backends

from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication

from user.models import Token


class TokenAuthentication(BaseTokenAuthentication):
	"""
	a substitute for rest_framework.authentication.TokenAuthentication class. It checks the expiry date
	of key as part of validation.
	"""
	model = Token

	def authenticate_credentials(self, key):
		invalid_token = _("Invalid session token, please login again to continue.")
		token_expired = _("Your session token has expired, please login again to continue.")
		account_disabled = _("Your account is disabled, please contact customer care.")

		try:
			token = self.model.objects.select_related('user').get(key=key)
		except self.model.DoesNotExist:
			raise exceptions.AuthenticationFailed(invalid_token)

		if timezone.now().__gt__(token.expiry):
			raise exceptions.AuthenticationFailed(token_expired)

		if not token.user.is_active:
			raise exceptions.AuthenticationFailed(account_disabled)

		return token.user, token


class DRFAuthBackend(backends.ModelBackend):
	"""
	override the authenticate method to implement login mechanism.
	"""
	def authenticate(self, username=None, password=None, **kwargs):
		UserModel = get_user_model()
		try:
			if username:
				user = UserModel.objects.get(username=username)
			else:
				user = UserModel.objects.get(**kwargs)
			if user.check_password(password):
				return user
		except UserModel.DoesNotExist:
			# Run the default password hasher once to reduce the timing
			# difference between an existing and a non-existing user (#20760).
			UserModel().set_password(password)
