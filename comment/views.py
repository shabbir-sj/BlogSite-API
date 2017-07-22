from django.http import Http404

from rest_framework import filters, exceptions
from rest_framework_filters.backends import DjangoFilterBackend
from rest_framework import generics

from comment.models import Comment
from comment.serializers import CommentSerializer
from post.models import Post
from user.mixins import AuthenticatedCreateViewMixin
from user.authentication import TokenAuthentication
from comment.filters import CommentFilter
from utils.utils import Utils, CustomPagination


class CommentListView(generics.ListCreateAPIView):

	authentication_classes = (TokenAuthentication,)
	filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
	filter_class = CommentFilter
	search_fields = ('desc',)
	ordering_fields = ('id', 'created_on', 'updated_on')
	ordering = '-id'
	pagination_class = CustomPagination

	def get_queryset(self):
		try:
			Post.objects.get(id=self.kwargs['pk'])
		except Exception as e:
			raise Http404
		return Comment.objects.filter(post=self.kwargs['pk'])

	def perform_create(self, serializer):
		serializer.validated_data['post_id'] = self.kwargs['pk']
		serializer.save()

	def get_serializer(self, *args, **kwargs):
		# Set the depth for serializer if requested
		depth = Utils.query_param_int(self.request, 'depth', 0)
		if depth is not None:
			kwargs['depth'] = depth

		serializer = CommentSerializer(*args, **kwargs)
		user = self.request.user
		serializer.auth_user = user
		return serializer


class CommentDetailView(AuthenticatedCreateViewMixin, generics.RetrieveUpdateDestroyAPIView):
	queryset = Comment.objects.all()
	serializer_class = CommentSerializer
