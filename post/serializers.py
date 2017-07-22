from rest_framework import serializers

from post.models import Post
from user.mixins import AuthenticatedSerializerMixin


class PostSerializer(AuthenticatedSerializerMixin, serializers.ModelSerializer):

	author = serializers.SerializerMethodField()

	def get_author(self, obj):
		if obj.user:
			return obj.user.get_author()
		return 'Anonymous'

	class Meta:
		model = Post
		fields = ('id', 'title', 'author', 'desc', 'created_on', 'updated_on')
		read_only_fields = ('created_on', 'updated_on')
