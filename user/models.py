import binascii
import os
from datetime import timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone

from utils.models import BlankModel


# Create your models here.


class CustomUser(AbstractUser):
	mobile = models.CharField(max_length=10, blank=True)
	is_email_verified = models.BooleanField(default=False)
	is_mobile_verified = models.BooleanField(default=False)

	class Meta:
		db_table = 'user'

	def delete_existing_tokens(self):
		# deletes existing tokens of user or logging out user of all devices
		Token.objects.filter(user=self).delete()

	def get_author(self):
		str = ''
		if self.first_name:
			str = self.first_name
		if self.last_name:
			str = str + ' ' + self.last_name

		return str

	def get_username(self):
		if self.email:
			return self.email
		if self.mobile:
			return self.mobile
		return self.username

	def make_active(self, auto_login=False, client_token=''):
		"""
		marks a user as active, sends welcome email and sms and if auto_login is True then creates an auth_token for
		device identified by client_token.
		:param auto_login: Boolean that marks if auto_login is enabled or not
		:param client_token: unique device identifier
		:return: user, token tuple
		"""
		self.is_active = True
		self.save()
		auth_token = None
		if auto_login:
			auth_token = Token.objects.create(user=self, client_token=client_token).key
		return auth_token

@python_2_unicode_compatible
class Token(BlankModel):
	"""
	model for auth token. inspired by rest_framework.authtoken.models.Token
	"""
	key = models.CharField(max_length=40, primary_key=True)
	user = models.ForeignKey(settings.AUTH_USER_MODEL)
	client_token = models.CharField(max_length=16, null=True)
	created = models.DateTimeField(auto_now_add=True)
	expiry = models.DateTimeField()

	class Meta:
		db_table = 'token'
		unique_together = ('user', 'client_token')

	def __str__(self):
		return self.key

	def build(self):
		self.key = Token.generate_key()
		self._set_expiry(30)

	def save(self, *args, **kwargs):
		if not self.key:
			self.build()
		return super().save(*args, **kwargs)

	def refresh(self, save=True):
		self._set_expiry(30, save=save)
		return self.key

	def expire(self, save=True):
		self._set_expiry(0, save=save)
		return None

	def _set_expiry(self, life_time, save=False):
		self.expiry = timezone.now() + timedelta(days=life_time)
		if save:
			self.save()

	@staticmethod
	def generate_key():
		return binascii.hexlify(os.urandom(20)).decode()