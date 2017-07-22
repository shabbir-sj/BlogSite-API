# from utils.utils import Utils
#
#
# class GetQuerySetMixin(object):
# 	def get_queryset(self):
# 		if self.queryset is None and self.model_class:
# 			self.queryset = self.model_class.objects.all()
# 		return super().get_queryset()
#
#
# class GetModelMixin(GetQuerySetMixin):
# 	model_class = None
#
# 	def get_requested_depth(self, request=None):
# 		return Utils.query_param_int(request or self.request, 'depth', 0)
#
# 	def get_serializer(self, *args, **kwargs):
# 		# See if client has requested only specific fields
# 		fields = Utils.query_param(self.request, 'fields')
# 		if fields:
# 			kwargs['fields'] = Utils.str_list(fields)
#
# 		# Set the depth for serializer if requested
# 		depth = self.get_requested_depth()
# 		if depth is not None:
# 			kwargs['depth'] = depth
# 		return super().get_serializer(*args, **kwargs)