import logging

import django.dispatch
from django.contrib.auth import get_user_model
from django.contrib.auth import user_logged_in
from django.db import transaction
from rest_framework import status, views
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework import generics

from user.utils import AuthUtils
from user.mixins import AuthenticatedViewMixin
from user.models import Token
from user.serializers import LoginSerializer, SignupSerializer

user_signed_up = django.dispatch.Signal(providing_args=["user", "request",])


class LoginView(mixins.CreateModelMixin, generics.GenericAPIView):
	"""
	Handles user login, returns access token on success. Updates users last login time.
	"""
	serializer_class = LoginSerializer

	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data['user']
		client_token = AuthUtils.get_client_token(self.request)
		token, created = Token.objects.get_or_create(user=user, client_token=client_token)
		if not created:
			if not AuthUtils.is_token_valid(token):
				# Token expired, refresh it..
				token.refresh()

		user_logged_in.send(sender=user.__class__, request=self.request, user=user)
		return Response({'token': token.key}, status=status.HTTP_200_OK)


class LogoutView(AuthenticatedViewMixin, views.APIView):
	def post(self, request, *args, **kwargs):
		"""
		Logs out the currently authenticated user identified by the auth-token in header, from current or all devices
		---
		parameters:
			- name: logout_all
			  description: set it to true if user wants to log out from all logged in devices.
			  type: string
			  paramType: query
		"""
		try:
			# delete current token
			request.auth.delete()

		except (APIException, Token.DoesNotExist) as e:
			return Response({'message': 'token invalid'}, status=status.HTTP_400_BAD_REQUEST)

		return Response({'message': 'Logged Out successfully'}, status=status.HTTP_200_OK)


class SignupView(mixins.CreateModelMixin, generics.GenericAPIView):
	"""
	Signs up a new user, Needs valid (unique)username and password
	Logs in the user on successful registration and returns the corresponding access_token
	"""
	serializer_class = SignupSerializer

	def post(self, request, *args, **kwargs):
		# First save the user
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		with transaction.atomic():
			user = serializer.save(is_active=True)
			if user:
				user_signed_up.send(sender=user.__class__, user=user, request=self.request)

		token = Token.objects.create(user=user, client_token=AuthUtils.get_client_token(self.request))
		return Response(data={'token': token.key}, status=status.HTTP_201_CREATED)
