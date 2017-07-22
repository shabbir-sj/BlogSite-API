from django.core.exceptions import FieldError
from rest_framework import exceptions
from django.utils.translation import ugettext_lazy as _

from user.utils import AuthUtils
from user.authentication import TokenAuthentication
from .permissions import IsAdmin, IsAuthor


class Validators:
	class UsernameMixin(object):
		def validate_username(self, value):
			value = AuthUtils.validate_username(value)
			if value:
				return value
			raise exceptions.ValidationError(_('need email or mobile'))

	class PasswordMixin(object):
		def validate_password(self, value):
			value = AuthUtils.validate_password(value)
			if value:
				return value
			raise exceptions.ValidationError(_('invalid password'))

	class NameMixin(object):
		def validate_first_name(self, value):
			# allow alphabets only
			if AuthUtils.validate_name(value) or value == '':
				return value
			raise exceptions.ValidationError(_('invalid first name'))

		def validate_last_name(self, value):
			# allow alphabets only
			if AuthUtils.validate_name(value) or value == '':
				return value
			raise exceptions.ValidationError(_('invalid last name'))

	class EmailMixin(object):
		def validate_email(self, value):
			# allowing for valid or empty email
			if AuthUtils.validate_email(value) or value == '':
				return value
			raise exceptions.ValidationError(_('invalid email address'))

	class MobileMixin(object):
		def validate_mobile(self, value):
			# allowing for valid or empty mobile number
			if AuthUtils.validate_mobile(value) or value == '':
				return value
			raise exceptions.ValidationError(_('invalid mobile number'))

	class LoginPermissionMixin(object):
		def is_login_allowed(self, user):
			return True


class AuthenticatedViewMixin(object):
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthor,)

	def get_serializer(self, *args, **kwargs):
		serializer = super().get_serializer(*args, **kwargs)

		user = self.request.user

		if self.request.method != "GET":
			assert user, _('auth user should exist')

		serializer.auth_user = user

		return serializer

	def get_queryset(self):
		query_set = super().get_queryset()

		if self.request.method == 'GET':
			return query_set

		try:
			return query_set.filter(user=self.request.user)
		except FieldError:
			return query_set

class AuthenticatedCreateViewMixin(AuthenticatedViewMixin):
	permission_classes = ()


class AuthenticatedSerializerMixin(object):
	def get_auth_user(self):
		user = getattr(self, 'auth_user', None)
		return user

	def to_internal_value(self, data):
		"""
		We override because we want to set the 'user' field implicitly to currently logged in user - we used to
		override validate() method for same job but it was too late as by then all other validation would have
		been run and in some cases it will fail because of missing 'user' field

		Also setting it here before validation might actually be better because it would be automatically
		dropped if there is no such ('user') field on model

		:param data: see super
		:return: see super
		"""
		value = super().to_internal_value(data)
		value['user'] = self.get_auth_user()
		return value

