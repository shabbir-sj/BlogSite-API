from django.db import models
from rest_framework import serializers
from rest_framework.utils import field_mapping
from rest_framework.fields import OrderedDict, SkipField, empty, CharField, JSONField as BaseJSONField, IntegerField
from rest_framework.relations import PrimaryKeyRelatedField

from comment.models import Comment
from post.models import Post
from post.serializers import PostSerializer
from user.mixins import AuthenticatedSerializerMixin


# Property descriptor to be used on the model instance for above field, similar to in-built
# class 'models.fields.related_descriptors.ForwardManyToOneDescriptor'
#
class IntegerAsForeignFieldDescriptor:
	def __init__(self, field):
		self.field = field

	def __get__(self, instance, instance_type=None):
		if instance is None:
			return None

		pk = getattr(instance, self.field.attname)
		if pk is None:
			return None

		# use the saved related data, but only if it hasn't changed
		if hasattr(self, 'value') and pk == getattr(self.value, self.field.remote_field_name):
			return self.value

		self.value = self.field.get_remote_obj(pk)
		return self.value

	def __set__(self, instance, value):
		if value is None and self.field.null is False:
			raise ValueError(
				'Cannot assign None: "%s.%s" does not allow null values.' %
				(instance._meta.object_name, self.field.name)
			)
		elif value is not None:
			if not isinstance(value, self.field.remote_model):
				raise ValueError(
					'Cannot assign "%r": "%s.%s" must be a "%s" instance.' % (
						value,
						instance._meta.object_name,
						self.field.name,
						self.field.remote_model._meta.object_name,
					)
				)

			pk = getattr(value, self.field.remote_field_name)
			setattr(instance, self.field.attname, pk)  # update the related field
			self.value = value  # Also save the related instance to avoid fetching it again in 'get'


# -----------------------------------------------
# Custom Integer Field class to be used for 'soft' foreign object reference - Soft because there is no
# actual referential integrity check/guarantee in DB, just in the code layer it ensures that the
# foreign object used actually exists in DB, and no reverse check either
#
# This should be used for fields which are supposed to be foreign-key to other model
# but are not defined such (no constrain in DB). For example, when the other model (table) is in foreign database,
#  like in case of Django's lack of support for cross-db foreign key
#
# Todo: Remove IntegerField dependency, could be derived from 'Field' directly allowing it to be used for non-int types
#
class IntegerAsForeignField(models.IntegerField):
	# default_error_messages = {
	# 	'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
	# 	'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
	# }

	def __init__(self, remote_model=None, remote_field_name='pk', **kwargs):
		self.remote_model = remote_model
		self.remote_field_name = remote_field_name
		super().__init__(**kwargs)

	def contribute_to_class(self, cls, name, virtual_only=False):
		super().contribute_to_class(cls, name, virtual_only=virtual_only)
		setattr(cls, self.name, IntegerAsForeignFieldDescriptor(self))

	def check(self, **kwargs):
		assert (
		self.remote_model and isinstance(self.remote_model, type) and issubclass(self.remote_model, models.Model)), \
			"Invalid parameter 'remote_model': should be a valid Model class found '{0}' instead".format(
				self.remote_model)

		assert issubclass(self.model, IntegerAsForeignFieldModelMixin), \
			"Model containing this field ('{0}=fieldfactory.IntegerAsForeignField(...)') must use 'IntegerAsForeignFieldModelMixin' as base".format(
				self.name)

		return super().check(**kwargs)

	def get_attname(self):
		return self.name if self.name.endswith('_id') else self.name + "_id"

	def get_attval(self, obj_or_pk):
		return obj_or_pk and (
		getattr(obj_or_pk, self.remote_field_name) if isinstance(obj_or_pk, self.remote_model) else obj_or_pk)

	def _raise_does_not_exist(self, value):
		pass

	# raise NotFound(_('{model} with {field}={value} does not exist').format(
	# 	model=self.remote_model.__name__,
	# 	field=self.remote_field_name,
	# 	value=value
	# ))

	def get_remote_obj(self, pk):
		try:
			return pk and self.remote_model.objects.get(**{self.remote_field_name: pk})
		except self.remote_model.DoesNotExist:
			self._raise_does_not_exist(pk)
		except (TypeError, ValueError):
			raise
		# raise NotFound(_('Incorrect type. Expected pk value ({0}), received {1}.').format(
		# 	self.remote_field_name, type(pk).__name__))


# Model mixin, use this if your model has any IntegerAsForeignField field
#
class IntegerAsForeignFieldModelMixin:
	def __init__(self, *args, **kwargs):
		# We override because we want to handle IntegerAsForeignField fields (which is actually IntegerField)
		# in same way as default ForeignField i.e accepting either of field.name ('fkobject=obj_or_pk')
		# or field.attname ('fkobject_id=obj_pk') as input
		#
		# Default implementation for IntegerField just looks for field.attname and ignores field.name
		# so here we just update kwargs with field.attname as well
		if kwargs:
			for field in self._meta.fields:
				if isinstance(field, IntegerAsForeignField):
					if field.name in kwargs and not field.attname in kwargs:
						kwargs[field.attname] = field.get_attval(kwargs.pop(field.name))

		super().__init__(*args, **kwargs)


# Serializer field class that would be used in conjunction with IntegerAsForeignField - is derived from ModelField
# instead of IntegerField as we need the 'model_field' value which is only passed to ModelField instance (see
# serializers.build_standard_field() method popping 'model_field' from kwargs for all but ModelField)
#
class IntegerPrimaryKeySerializerField(serializers.ModelField):
	def __init__(self, model_field, **kwargs):
		# our model field is actually an IntegerField which has min/max attribute, ignore it
		kwargs.pop('min_value', None)
		kwargs.pop('max_value', None)
		super().__init__(model_field, **kwargs)

	def get_nested_serializer_class(self):
		parent = self.parent

		# For 'applied_depth' see utils.serializers.ModelSerializer
		cur_depth = getattr(parent, 'applied_depth', None) or getattr(parent.Meta, 'depth', None)
		if cur_depth and int(cur_depth) >= 1:
			# depth > 0, we need to provide serializer for expanding the field
			# Check if parent serializer specifies any custom serializer for this field via 'get_nested_field_serializer_class'
			# otherwise create and return the the default one
			get_nested_serializers = getattr(parent, 'get_nested_field_serializer_class', None)
			if get_nested_serializers and callable(get_nested_serializers):
				ser = get_nested_serializers(self.field_name)
				if ser:
					# found one, create a copy with proper depth
					class NestedSerializer(ser):
						class Meta(ser.Meta):
							ser.Meta.depth = cur_depth - 1

					return NestedSerializer

			# No custom serializer, lets just the use the default one
			class NestedSerializer(serializers.ModelSerializer):
				class Meta:
					model = self.model_field.remote_model
					depth = cur_depth - 1

			return NestedSerializer

	def to_internal_value(self, data):
		data = super().to_internal_value(data)
		return self.model_field.get_remote_obj(data)

	def to_representation(self, value):
		# value is complete model instance and not this field value, see ModelField for details

		# handle depth > 0
		nested_serializer_class = self.get_nested_serializer_class()
		if nested_serializer_class:
			return nested_serializer_class(getattr(value, self.field_name)).data

		return self.model_field.value_from_object(value)


# Add to standard mapping...
serializers.ModelSerializer.serializer_field_mapping[IntegerAsForeignField] = IntegerPrimaryKeySerializerField


def serializer_skip_null_to_representation(self, instance):
	"""
	Same as base class implementation but skips null values.

	Object instance -> Dict of primitive datatypes.
	"""
	ret = OrderedDict()
	fields = [field for field in self.fields.values()]

	depth = self.applied_depth if hasattr(self, 'applied_depth') else getattr(self.Meta, 'depth', 0) if hasattr(self, 'Meta') else 0
	for field in fields:
		try:
			attribute = field.get_attribute(instance)
		except SkipField:
			continue

		# Keeps only if it is non-null
		if attribute is not None:
			value = field.to_representation(attribute)
			if value is not None:
				if (depth == 0 or isinstance(value, int)) and isinstance(field, (
				PrimaryKeyRelatedField, IntegerPrimaryKeySerializerField)):
					ret[field.field_name + '_id'] = value
				else:
					ret[field.field_name] = value
				# else:
				# 	if isinstance(field, rest_framework.fields.IntegerField) or isinstance(field,
				# 			rest_framework.fields.FloatField):
				# 		ret[field.field_name] = 1234567890123456
				# 	else:
				# 		ret[field.field_name] = 'THIS FIELD IS NULL'
	return ret


serializers.Serializer.to_representation = serializer_skip_null_to_representation


class CommentSerializer(AuthenticatedSerializerMixin, serializers.ModelSerializer):

	author = serializers.SerializerMethodField()

	def get_author(self, obj):
		if obj.user:
			return obj.user.get_author()
		return 'Anonymous'

	class Meta:
		model = Comment
		fields = ('id', 'post', 'author', 'desc', 'created_on', 'updated_on', 'comment')
		read_only_fields = ('user', 'post', 'created_on', 'updated_on')
		ignore_depth_fields = ('user',)

	# maximum allowed depth for this serializer, relatively safe default of 1 (0?) :-) override if you need more
	# Note that drf has its own hard max set at 10 which can't be bypassed
	max_depth = 1

	# List of fields that are NOT allowed to expand even on depth > 0
	# ignore_depth_fields = ('user',)

	# field_name vs. custom SerializerClass mapping
	# nested_field_serializers = {
	# 	# 'field_name': SerializerClass
	# }

	@classmethod
	def _get_meta_or_class_property(cls, name, default=None):
		"""
		:param name: property name
		:return: Returns the Meta class property if defined, otherwise try on self class
		"""
		value = getattr(cls.Meta, name, None)
		if value is None:
			value = getattr(cls, name, default)
		return value

	@classmethod
	def get_nested_field_serializer_class(cls, field_name, default_field_class=None):
		d = cls._get_meta_or_class_property('nested_field_serializers')
		return d.get(field_name, default_field_class) if d else default_field_class

	def __init__(self, *args, **kwargs):
		self.requested_fields = kwargs.pop('fields', None)
		self.requested_depth = kwargs.pop('depth', None)
		super().__init__(*args, **kwargs)

		# Enforce max_depth, in case of Meta.depth (set in code) complain immediately..
		max_depth = self._get_meta_or_class_property('max_depth')
		depth = getattr(self.Meta, 'depth', 0)
		assert max_depth is None or depth <= max_depth, "depth={0} is more than max_depth={1}".format(depth, max_depth)

		# ..but for requested_depth (set by client) silently cap it to max
		if self.requested_depth and self.requested_depth > max_depth:
			self.requested_depth = max_depth

	@property
	def applied_depth(self):
		if self.requested_depth:
			return self.requested_depth
		return getattr(self.Meta, 'depth', 0)

	def build_nested_field(self, field_name, relation_info, nested_depth):
		"""
		Create nested fields for forward and reverse relationships

		We override to specify our own Serializer classes for nested field if given (via 'nested_field_serializers'
		 mapping or nested_field_serializers() method override)

		Also checks if the requested nested field is marked as 'never-expand' fields in which case we simply
		  route to non-depth path 'build_relational_field' (see super's method)
		"""

		# See if the field is allowed to expand at all, either because we hit the max-depth or because
		# this field itself is not allowed to - break right away it not
		max_depth = self._get_meta_or_class_property('max_depth', default=1)
		assert nested_depth <= max_depth, "depth={0} is more than max_depth={1}".format(nested_depth, max_depth)

		if field_name in self._get_meta_or_class_property('ignore_depth_fields', default=[]):
			return self.build_relational_field(field_name, relation_info)

		# Need to expand, see if there is a Serializer set explicitly for this field..
		field_class = self.get_nested_field_serializer_class(field_name)
		if field_class:
			# We create a subclass on the fly as we don't want original's Meta.depth to be messed-up
			class NestedSerializer(field_class):
				class Meta(field_class.Meta):
					depth = nested_depth - 1

			return NestedSerializer, field_mapping.get_nested_relation_kwargs(relation_info)

		# Nothing special to do, just pass on to super
		return super().build_nested_field(field_name, relation_info, nested_depth)

	def get_fields(self):
		"""
		We override to apply 'depth' requested by client just before the call to super (and reset it back before returning)
		:return:
		"""
		if self.requested_depth is not None:
			default_depth = getattr(self.Meta, 'depth', None)
			if default_depth != self.requested_depth:
				self.Meta.depth = self.requested_depth
				fields = super().get_fields()
				if default_depth is not None:
					self.Meta.depth = default_depth
				else:
					delattr(self.Meta, 'depth')
				return fields
		return super().get_fields()
