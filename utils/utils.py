from rest_framework.pagination import PageNumberPagination


class Utils:
	@staticmethod
	def query_param(request, key, default_value=None):
		qp = getattr(request, 'query_params', None)
		return DictUtils.get(qp, key, default_value) if qp else default_value

	@staticmethod
	def query_param_int(request, key, minimum=None, maximum=None):
		depth = Utils.query_param(request, key)
		if depth:
			try:
				depth = int(depth)
				if minimum is not None and depth < minimum:
					depth = minimum
				if maximum is not None and depth > maximum:
					depth = maximum

				return depth
			except ValueError:
				# logger.warn('Invalid integer param, {0}={1}, ignoring'.format(key, depth))
				pass

	@staticmethod
	def str_list(comma_separated_strs):
		if not comma_separated_strs:
			return None if comma_separated_strs is None else []

		comma_separated_strs = comma_separated_strs.strip('[{( )}]')
		strs = [s.strip() for s in comma_separated_strs.split(',') if s]
		strs = [s for s in strs if s]
		return strs

	@staticmethod
	def int_list(comma_separated_ints):
		if not comma_separated_ints:
			return None if comma_separated_ints is None else []

		nos = comma_separated_ints
		if type(comma_separated_ints) is not list:
			comma_separated_ints = comma_separated_ints.strip('[{( )}]')
			nos = [n.strip() for n in comma_separated_ints.split(',') if n]

		ret = []
		for n in nos:
			if n:
				try:
					ret.append(int(n))
				except ValueError:
					pass
		return ret


class DictUtils:
	@staticmethod
	def get(d, key, default_val):
		try:
			return d[key]
		except KeyError as e:
			return default_val


class CustomPagination(PageNumberPagination):
	page_size = 5
	page_size_query_param = 'page-size'
	max_page_size = 1000