from rest_framework import filters, exceptions
from rest_framework_filters.backends import DjangoFilterBackend
from rest_framework import generics

from post.models import Post
from post.filters import PostFilter
from post.serializers import PostSerializer
from user.mixins import AuthenticatedCreateViewMixin
from utils.utils import CustomPagination


class PostListView(AuthenticatedCreateViewMixin, generics.ListCreateAPIView):
	filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
	filter_class = PostFilter
	search_fields = ('title', 'desc')
	ordering_fields = ('id', 'created_on', 'updated_on')
	queryset = Post.objects.all()
	serializer_class = PostSerializer
	ordering = '-id'
	pagination_class = CustomPagination


class PostDetailView(AuthenticatedCreateViewMixin, generics.RetrieveUpdateDestroyAPIView):
	queryset = Post.objects.all()
	serializer_class = PostSerializer
