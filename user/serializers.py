
from django.contrib.auth import get_user_model, authenticate
from django.core.validators import MaxLengthValidator
from django.core.validators import ValidationError
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, exceptions

from user.utils import AuthUtils
from user.mixins import Validators


class LoginSerializer(Validators.LoginPermissionMixin, serializers.Serializer):
	"""
	Serializer for author login.
	"""
	username = serializers.CharField()
	password = serializers.CharField()

	def validate(self, data):
		"""
		allowing login using email/mobile/username.
		"""
		try:
			username = AuthUtils.check_for_param(data, 'username')
			password = AuthUtils.check_for_param(data, 'password')
			MaxLengthValidator(limit_value=40)(password)
		except exceptions.ValidationError as e:
			raise ValidationError(_('no username or password'))
		except ValidationError as e:
			raise ValidationError(_('invalid username or password'))

		email, mobile = AuthUtils.validate_email(username), AuthUtils.validate_mobile(username)

		# setting username field based on provided username field value.
		if email:
			kwargs = {'email': username}
		elif mobile:
			kwargs = {'mobile': username}
		else:
			kwargs = {'username': username}

		user = authenticate(password=password, **kwargs)
		if not user:
			raise exceptions.AuthenticationFailed()

		data['user'] = user
		return data


class SignupSerializer(Validators.EmailMixin, Validators.MobileMixin, Validators.PasswordMixin,
                       Validators.NameMixin, serializers.Serializer):
	"""
	Serializer for signing up a new user
	"""
	email = AuthUtils.default_email_field()
	mobile = AuthUtils.default_mobile_field()
	password = AuthUtils.default_password_field()
	first_name = serializers.CharField(allow_blank=True, max_length=30, required=False)
	last_name = serializers.CharField(allow_blank=True, max_length=30, required=False)

	def validate(self, data):
		try:
			email = AuthUtils.check_for_param(data, 'email')
			mobile = data.get('mobile')
			AuthUtils.check_for_param(data, 'password')

			if email:
				AuthUtils.check_for_uniqueness(email=email)
			if mobile:
				AuthUtils.check_for_uniqueness(mobile=mobile)
		except Exception as e:
			raise ValidationError(_('user exists'))

		return data

	def create(self, validated_data):
		try:
			username = AuthUtils.get_username()
			password = validated_data['password']
			email = validated_data['email']
			mobile = validated_data.get('mobile', '')
			is_active = validated_data.get('is_active', True)
			first_name = validated_data.get('first_name', '')
			last_name = validated_data.get('last_name', '')

			is_email_verified = validated_data.get('is_email_verified', False)
			is_mobile_verified = validated_data.get('is_mobile_verified', False)

			UserModel = get_user_model()
			user = UserModel.objects.create_user(
				username=username, email=email, mobile=mobile, password=password,
				is_active=is_active, first_name=first_name, last_name=last_name,
				is_email_verified=is_email_verified, is_mobile_verified=is_mobile_verified
			)
			return user

		except Exception as e:
			pass
