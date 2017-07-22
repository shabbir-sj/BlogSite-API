import datetime
import rest_framework_filters as filters

# from utils import dateutils


def add_date_filtering(cls):
	"""
	Adds date-filtering to filtering-class 'cls'.
	Fields provided to cls.Meta.date_fields are given date-filtering for =, __lte, __gte
	Fields provided to cls.Meta.date_range_fields are given DTR date-range-filtering for options like: Today, Last 7 Days
	:param cls: Filtering class
	"""
	if hasattr(cls.Meta, 'date_fields'):
		for field in cls.Meta.date_fields:
			filter_update = {
				field: filters.DateFilter(name=field, lookup_type='contains'),
				field + '__lte': filters.DateTimeFilter(name=field, lookup_type='lte'),
				field + '__gte': filters.DateTimeFilter(name=field, lookup_type='gte')
			}
			cls.declared_filters.update(filter_update)
			cls.base_filters.update(filter_update)


# class DateTimeFilter(object):
# 	"""
# 	Represents DateTime field as Date and applies filtering as Date field.
# 	Use this class if the field type is DateTime but filtering needs to be applied as Date field.
# 	"""
#
# 	@staticmethod
# 	def date__gte(queryset, value, field):
# 		date_time = dateutils.get_date_time(value)
# 		if '__gte' not in field:
# 			field += '__gte'
#
# 		kwargs = {field: date_time}
# 		return queryset.filter(**kwargs)
#
# 	@staticmethod
# 	def date__lt(queryset, value, field):
# 		date_time = dateutils.get_date_time(value) + datetime.timedelta(days=1)
# 		if '__lt' not in field:
# 			field += '__lt'
#
# 		kwargs = {field: date_time}
# 		return queryset.filter(**kwargs)
#
# 	@staticmethod
# 	def date(queryset, value, field):
# 		queryset = DateTimeFilter.date__gte(queryset, value, field)
# 		return DateTimeFilter.date__lt(queryset, value, field)