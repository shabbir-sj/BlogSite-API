import rest_framework_filters as filters
# from django.contrib.auth import get_user_model

from utils.utils import Utils
from utils.filters import add_date_filtering
from comment.models import Comment


class CommentFilter(filters.FilterSet):
	desc__icontains = filters.CharFilter(name='desc', lookup_type='icontains')
	user_ids = filters.MethodFilter(action='userid_filter')

	def userid_filter(self, name, queryset, value):
		return queryset.filter(user__pk__in=Utils.int_list(value))


	# def userid_filter(self, name, queryset, value):
	# 	value = Utils.int_list(value)
	# 	rel_queryset = get_user_model().objects.all()
	#
	# 	kwargs = {'pk__in': value}
	# 	comment_list = rel_queryset.filter(**kwargs)
	# 	comment_idlist = comment_list.values_list('comment_user__pk', flat=True)
	# 	return queryset.filter(pk__in=comment_idlist)

	class Meta:
		model = Comment
		fields = ('desc',)
		date_fields = ('created_on', 'updated_on')


add_date_filtering(CommentFilter)
