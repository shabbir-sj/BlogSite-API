from datetime import timedelta

import pytz
from django.utils import timezone
from rest_framework import exceptions


IST = pytz.timezone('Asia/Kolkata')


def _get_date_parts(date_str):
	separator = ' '
	if '-' in date_str:
		separator = '-'
	if '/' in date_str:
		separator = '/'

	y, m, d = map(int, date_str.split(separator))
	return y, m, d


def get_date_time(date_str):
	try:
		y, m, d = _get_date_parts(date_str)
		return timezone.datetime(y, m, d)

	except ValueError:
		raise exceptions.APIException("Invalid date provided.")


def utc_to_ist(utc_datetime=None):
	if not utc_datetime:
		utc_datetime = timezone.now()
	return timezone.localtime(utc_datetime, IST)


def time_in_ist(utc_datetime=None):
	return utc_to_ist(utc_datetime).time()


def date_in_ist(utc_datetime=None):
	return utc_to_ist(utc_datetime).date()


def time_is_future(time, days=0, hours=0, minutes=0, seconds=0, milliseconds=1, ref_time=None):
	if not time:
		return False

	ref_time = ref_time or timezone.now()
	delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
	return time.__ge__(ref_time + delta)


def time_is_past(time, days=0, hours=0, minutes=0, seconds=0, milliseconds=1, ref_time=None):
	if not time:
		return False

	ref_time = ref_time or timezone.now()
	delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
	return time.__le__(ref_time - delta)


def time_is_same(time, ref_time=None, minutes=0, seconds=0, milliseconds=10, microseconds=0, ):
	if not time or not ref_time:
		return False

	delta = timedelta(minutes=minutes, seconds=seconds, milliseconds=milliseconds, microseconds=microseconds)
	return abs(time - ref_time).__le__(delta)


class DateRange:
	def __init__(self, *args, **kwargs):
		if len(args) == 1:
			if isinstance(args[0], type(self)):
				self.start = args[0].start
				self.end = args[0].end
			else:
				tuple_ = args[0]
				assert isinstance(tuple_, tuple), "You should either pass 'start' and 'end' both or a tuple containing them"
				self.start = tuple_[0]
				self.end = tuple_[1]
		elif len(args) == 2:
			assert len(args) == 2, "You should either pass 'start' and 'end' both or a tuple containing them"
			self.start = args[0]
			self.end = args[1]
		else:
			assert len(args) == 0 and 'start' in kwargs and 'end' in kwargs, "You should either pass 'start' and 'end' both or a tuple containing them"
			self.start = kwargs['start']
			self.end = kwargs['end']

		assert self.start <= self.end, "'end' cannot be less than 'start'"

	@classmethod
	def _start(cls, value):
		if isinstance(value, tuple):
			return value[0]
		elif isinstance(value, cls):
			return value.start
		return value

	@classmethod
	def _end(cls, value):
		if isinstance(value, tuple):
			return value[1]
		elif isinstance(value, cls):
			return value.end
		return value

	def __lt__(self, other):
		return self.start < self._start(other)

	def __le__(self, other):
		return self.start <= self._start(other)

	def __gt__(self, other):
		return self.end > self._end(other)

	def __ge__(self, other):
		return self.end >= self._end(other)

	def __add__(self, other):
		if isinstance(other, (type(self), tuple)):
			return self.union(other)
		return DateRange(self.start + other, self.end + other)

	def __radd__(self, other):
		return self.__add__(other)

	def __sub__(self, other):
		return DateRange(self.start - other, self.end - other)

	def __rsub__(self, other):
		return self.__sub__(other)

	def __len__(self):
		return (self.end - self.start).days + 1

	def __repr__(self):
		return super().__repr__() + ': ' + self.__str__()

	def __str__(self):
		return '(start={0}, end={1})'.format(self.start, self.end)

	def intersection(self, other):
		if isinstance(other, tuple):
			other = DateRange(other[0], other[1])

		start = max(self.start, other.start)
		end = min(self.end, other.end)
		return None if start > end else DateRange(start, end)

	def union(self, other):
		if isinstance(other, tuple):
			other = DateRange(other[0], other[1])

		start = min(self.start, other.start)
		end = max(self.end, other.end)
		return DateRange(start, end)

	def days_from_today(self):
		today = date_in_ist()

		past = (self.end - today).days
		future = (self.start - today).days
		return past if past < 0 else future if future > 0 else 0

	def is_future(self):
		return self.start > date_in_ist()