import rest_framework_filters as filters

from utils.utils import Utils
from utils.filters import add_date_filtering
from post.models import Post


class PostFilter(filters.FilterSet):
	title__icontains = filters.CharFilter(name='title', lookup_type='icontains')
	desc__icontains = filters.CharFilter(name='desc', lookup_type='icontains')
	user_ids = filters.MethodFilter(action='userid_filter')

	def userid_filter(self, name, queryset, value):
		return queryset.filter(user__pk__in=Utils.int_list(value))

	# def created_on_filter(self, name, queryset, value):
	# 	return DateTimeFilter.date(queryset, value, 'created_on')
	#
	# def updated_on_filter(self, name, queryset, value):
	# 	return DateTimeFilter.date(queryset, value, 'updated_on')

	class Meta:
		model = Post
		fields = ('title', 'desc')
		date_fields = ('created_on', 'updated_on')


add_date_filtering(PostFilter)
