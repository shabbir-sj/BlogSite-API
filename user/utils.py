import logging
import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers, exceptions, status

logger = logging.getLogger(__name__)

validate_email = EmailValidator(_('invalid email id'), status.HTTP_400_BAD_REQUEST)

# first-name, last-name regex
name_re = re.compile(r'^[a-zA-Z ,.\'-]+$', )
validate_name = RegexValidator(name_re, _('invalid name'), status.HTTP_400_BAD_REQUEST)

# mobile regex
mobile_re = re.compile(r'^[7-9][0-9]{9}$')
validate_mobile = RegexValidator(mobile_re, _('invalid mobile number'), status.HTTP_400_BAD_REQUEST)


class AuthUtils:
	@staticmethod
	def validate_username(username):
		# Enforce acceptable username format here
		email_or_mobile = AuthUtils.validate_email(username) or AuthUtils.validate_mobile(username)
		return username if email_or_mobile else None

	@staticmethod
	def validate_password(password):
		# Enforce acceptable password format here: Only alpha-numeric+[some special chars] ??
		return password

	@staticmethod
	def validate_email(email):
		# Enforce acceptable email format here
		try:
			validate_email(email)
		except DjangoValidationError as e:
			return None
		return email

	@staticmethod
	def validate_mobile(mobile):
		# Enforce acceptable mobile format here
		try:
			validate_mobile(mobile)
		except DjangoValidationError as e:
			return None
		return mobile

	@staticmethod
	def validate_name(name):
		try:
			validate_name(name)
		except DjangoValidationError as e:
			return None
		return name

	@staticmethod
	def check_for_param(data, param):
		value = data.get(param)
		if not value:
			raise exceptions.ValidationError(_('invalid parameter') + param)
		return value

	@staticmethod
	def check_for_uniqueness(**kwargs):
		UserModel = get_user_model()
		try:
			UserModel.objects.get(**kwargs)
			key = 'email' if 'email' in kwargs else 'mobile'
			msg = _('{0}_already_registered', key)
			raise exceptions.ValidationError(msg)
		except UserModel.DoesNotExist:
			pass  # we are good to go

		return True

	@staticmethod
	def check_for_user(username):
		UserModel = get_user_model()
		email, mobile = AuthUtils.validate_email(username), AuthUtils.validate_mobile(username)

		if email:
			kwargs = {'email': username}
		elif mobile:
			kwargs = {'mobile': username}
		else:
			kwargs = {'username': username}

		try:
			return UserModel.objects.get(**kwargs)
		except UserModel.DoesNotExist:
			raise exceptions.NotFound(_('user_does_not_exist'))

	@staticmethod
	def is_token_valid(token):
		return timezone.now().__lt__(token.expiry)

	@staticmethod
	def db_table_name(table):
		return 'auth_' + table

	@staticmethod
	def get_username(length=None):
		length = int(8) if not length else length
		return get_random_string(length=length)

	@staticmethod
	def default_username_field():
		return serializers.CharField(min_length=4, max_length=75)

	@staticmethod
	def default_password_field():
		return serializers.CharField(min_length=8,
		                             max_length=40,
		                             style={'input_type': 'password'}
		                             )

	@staticmethod
	def default_email_field(required=False):
		return serializers.CharField(min_length=5, max_length=254, required=required)

	@staticmethod
	def default_mobile_field(required=False):
		return serializers.CharField(min_length=10, max_length=10, required=required)

	@staticmethod
	def check_email_or_mobile_present(attrs):
		try:
			email = AuthUtils.check_for_param(attrs, 'email')
		except exceptions.ValidationError as e1:
			try:
				mobile = AuthUtils.check_for_param(attrs, 'mobile')
				return None, mobile
			except exceptions.ValidationError as e2:
				detail = {
					'email': e1.detail,
					'mobile': e2.detail
				}
				raise exceptions.ValidationError(detail=detail)
		else:
			try:
				mobile = AuthUtils.check_for_param(attrs, 'mobile')
			except exceptions.ValidationError:
				mobile = None
			return email, mobile

	@staticmethod
	def get_client_token(request):
		if hasattr(request, '_request'):
			request = getattr(request, '_request')

		if hasattr(request, 'META'):
			return request.META.get('HTTP_CLIENT_TOKEN', '')

		return ''

