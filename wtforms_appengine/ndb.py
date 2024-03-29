"""
Form generation utilities for App Engine's new ``ndb.Model`` class.

The goal of ``model_form()`` is to provide a clean, explicit and predictable
way to create forms based on ``ndb.Model`` classes. No malabarism or black
magic should be necessary to generate a form for models, and to add custom
non-model related fields: ``model_form()`` simply generates a form class
that can be used as it is, or that can be extended directly or even be used
to create other forms using ``model_form()``.

Example usage:

.. code-block:: python

   from google.appengine.ext import ndb
   from wtforms_appengine.ndb import model_form

   # Define an example model and add a record.
   class Contact(ndb.Model):
       name = ndb.StringProperty(required=True)
       city = ndb.StringProperty()
       age = ndb.IntegerProperty(required=True)
       is_admin = ndb.BooleanProperty(default=False)

   new_entity = Contact(key_name='test', name='Test Name', age=17)
   new_entity.put()

   # Generate a form based on the model.
   ContactForm = model_form(Contact)

   # Get a form populated with entity data.
   entity = Contact.get_by_key_name('test')
   form = ContactForm(obj=entity)

Properties from the model can be excluded from the generated form, or it can
include just a set of properties. For example:

.. code-block:: python

   # Generate a form based on the model, excluding 'city' and 'is_admin'.
   ContactForm = model_form(Contact, exclude=('city', 'is_admin'))

   # or...

   # Generate a form based on the model, only including 'name' and 'age'.
   ContactForm = model_form(Contact, only=('name', 'age'))

The form can be generated setting field arguments:

.. code-block:: python

   ContactForm = model_form(Contact, only=('name', 'age'), field_args={
       'name': {
           'label': 'Full name',
           'description': 'Your name',
       },
       'age': {
           'label': 'Age',
           'validators': [validators.NumberRange(min=14, max=99)],
       }
   })

The class returned by ``model_form()`` can be used as a base class for forms
mixing non-model fields and/or other model forms. For example:

.. code-block:: python

   # Generate a form based on the model.
   BaseContactForm = model_form(Contact)

   # Generate a form based on other model.
   ExtraContactForm = model_form(MyOtherModel)

   class ContactForm(BaseContactForm):
       # Add an extra, non-model related field.
       subscribe_to_news = f.BooleanField()

       # Add the other model form as a subform.
       extra = f.FormField(ExtraContactForm)

The class returned by ``model_form()`` can also extend an existing form
class:

.. code-block:: python

   class BaseContactForm(Form):
       # Add an extra, non-model related field.
       subscribe_to_news = f.BooleanField()

   # Generate a form based on the model.
   ContactForm = model_form(Contact, base_class=BaseContactForm)

"""
from wtforms import fields as f
from wtforms import Form
from wtforms import validators

from .fields import GeoPtPropertyField
from .fields import IntegerListPropertyField
from .fields import JsonPropertyField
from .fields import KeyPropertyField
from .fields import RepeatedKeyPropertyField
from .fields import StringListPropertyField


def get_StringField(kwargs):
    """
    Returns a ``StringField``, applying the ``ndb.StringProperty`` length limit
    of 500 bytes.
    """
    kwargs["validators"].append(validators.length(max=500))
    return f.StringField(**kwargs)


def get_IntegerField(kwargs):
    """
    Returns an ``IntegerField``, applying the ``ndb.IntegerProperty`` range
    limits.
    """
    v = validators.NumberRange(min=-0x8000000000000000, max=0x7FFFFFFFFFFFFFFF)
    kwargs["validators"].append(v)
    return f.IntegerField(**kwargs)


class ModelConverterBase:
    def __init__(self, converters=None):
        """
        Constructs the converter, setting the converter callables.

        :param converters:
            A dictionary of converter callables for each property type. The
            callable must accept the arguments (model, prop, kwargs).
        """
        self.converters = {}

        for name in dir(self):
            if not name.startswith("convert_"):
                continue
            self.converters[name[8:]] = getattr(self, name)

    def convert(self, model, prop, field_args):
        """
        Returns a form field for a single model property.

        :param model:
            The ``db.Model`` class that contains the property.
        :param prop:
            The model property: a ``db.Property`` instance.
        :param field_args:
            Optional keyword arguments to construct the field.
        """

        prop_type_name = type(prop).__name__

        # check for generic property
        if prop_type_name == "GenericProperty":
            # try to get type from field args
            generic_type = field_args.get("type") if field_args else None

            if generic_type:
                prop_type_name = field_args.get("type")
            # if no type is found, the generic property uses string set in
            # convert_GenericProperty

        kwargs = {
            "label": (prop._verbose_name or prop._code_name.replace("_", " ").title()),
            "default": prop._default,
            "validators": [],
        }
        if field_args:
            kwargs.update(field_args)

        if prop._required and prop_type_name not in self.NO_AUTO_REQUIRED:
            kwargs["validators"].append(validators.required())

        choices = kwargs.get("choices", None) or prop._choices
        if choices:
            # Use choices in a select field.
            kwargs["choices"] = [(v, v) for v in choices]
            if prop._repeated:
                return f.SelectMultipleField(**kwargs)
            else:
                return f.SelectField(**kwargs)

        else:
            converter = self.converters.get(prop_type_name, None)
            if converter is not None:
                return converter(model, prop, kwargs)
            else:
                return self.fallback_converter(model, prop, kwargs)


class ModelConverter(ModelConverterBase):
    """
    Converts properties from a ``ndb.Model`` class to form fields.

    Default conversions between properties and fields:

    +====================+===================+==============+==================+
    | Property subclass  | Field subclass    | datatype     | notes            |
    +====================+===================+==============+==================+
    | StringProperty     | StringField       | unicode      | TextArea         | repeated support
    |                    |                   |              | if multiline     |
    +--------------------+-------------------+--------------+------------------+
    | BooleanProperty    | BooleanField      | bool         |                  |
    +--------------------+-------------------+--------------+------------------+
    | IntegerProperty    | IntegerField      | int or long  |                  | repeated support
    +--------------------+-------------------+--------------+------------------+
    | FloatProperty      | StringField       | float        |                  |
    +--------------------+-------------------+--------------+------------------+
    | DateTimeProperty   | DateTimeField     | datetime     | skipped if       |
    |                    |                   |              | auto_now[_add]   |
    +--------------------+-------------------+--------------+------------------+
    | DateProperty       | DateField         | date         | skipped if       |
    |                    |                   |              | auto_now[_add]   |
    +--------------------+-------------------+--------------+------------------+
    | TimeProperty       | DateTimeField     | time         | skipped if       |
    |                    |                   |              | auto_now[_add]   |
    +--------------------+-------------------+--------------+------------------+
    | TextProperty       | TextAreaField     | unicode      |                  |
    +--------------------+-------------------+--------------+------------------+
    | GeoPtProperty      | StringField       | db.GeoPt     |                  |
    +--------------------+-------------------+--------------+------------------+
    | KeyProperty        | KeyProperyField   | ndb.Key      |                  |
    +--------------------+-------------------+--------------+------------------+
    | BlobKeyProperty    | None              | ndb.BlobKey  | always skipped   |
    +--------------------+-------------------+--------------+------------------+
    | UserProperty       | None              | users.User   | always skipped   |
    +--------------------+-------------------+--------------+------------------+
    | StructuredProperty | None              | ndb.Model    | always skipped   |
    +--------------------+-------------------+--------------+------------------+
    | LocalStructuredPro | None              | ndb.Model    | always skipped   |
    +--------------------+-------------------+--------------+------------------+
    | JsonProperty       | JsonPropertyField | datastucture |                  |
    +--------------------+-------------------+--------------+------------------+
    | PickleProperty     | None              | bytedata     | always skipped   |
    +--------------------+-------------------+--------------+------------------+
    | GenericProperty    | None              | generic      | always skipped   |
    +--------------------+-------------------+--------------+------------------+
    | ComputedProperty   | none              |              | always skipped   |
    +--------------------+-------------------+--------------+------------------+
    | _ClassKeyProperty  | none              |              | always skipped   |
    +====================+===================+==============+==================+

    """  # noqa

    # Don't automatically add a required validator for these properties
    NO_AUTO_REQUIRED = frozenset(
        ["ListProperty", "StringListProperty", "BooleanProperty"]
    )

    def convert_StringProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.StringProperty``."""
        if prop._repeated:
            return StringListPropertyField(**kwargs)
        kwargs["validators"].append(validators.length(max=500))
        return get_StringField(kwargs)

    def convert_BooleanProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.BooleanProperty``."""
        return f.BooleanField(**kwargs)

    def convert_IntegerProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.IntegerProperty``."""
        if prop._repeated:
            return IntegerListPropertyField(**kwargs)
        return get_IntegerField(kwargs)

    def convert_FloatProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.FloatProperty``."""
        return f.FloatField(**kwargs)

    def convert_DateTimeProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.DateTimeProperty``."""
        if prop._auto_now or prop._auto_now_add:
            return None

        kwargs.setdefault("format", "%Y-%m-%d %H:%M:%S")
        return f.DateTimeField(**kwargs)

    def convert_DateProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.DateProperty``."""
        if prop._auto_now or prop._auto_now_add:
            return None

        kwargs.setdefault("format", "%Y-%m-%d")
        return f.DateField(**kwargs)

    def convert_TimeProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.TimeProperty``."""
        if prop._auto_now or prop._auto_now_add:
            return None

        kwargs.setdefault("format", "%H:%M:%S")
        return f.DateTimeField(**kwargs)

    def convert_UserProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.UserProperty``."""
        return None

    def convert_StructuredProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.StructuredProperty``."""
        return None

    def convert_LocalStructuredProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.LocalStructuredProperty``."""
        return None

    def convert_JsonProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.JsonProperty``."""
        return JsonPropertyField(**kwargs)

    def convert_PickleProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.PickleProperty``."""
        return None

    def convert_GenericProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.GenericProperty``."""
        kwargs["validators"].append(validators.length(max=500))
        return get_StringField(kwargs)

    def convert_BlobKeyProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.BlobKeyProperty``."""
        return f.FileField(**kwargs)

    def convert_TextProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.TextProperty``."""
        return f.TextAreaField(**kwargs)

    def convert_ComputedProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.ComputedProperty``."""
        return None

    def convert_GeoPtProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.GeoPtProperty``."""
        return GeoPtPropertyField(**kwargs)

    def convert_KeyProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.KeyProperty``."""
        if "reference_class" not in kwargs or "query" not in kwargs:
            try:
                reference_class = prop._kind
            except AttributeError:
                reference_class = prop._reference_class

            if isinstance(reference_class, str):
                # This assumes that the referenced module is already imported.
                try:
                    reference_class = model._kind_map[reference_class]
                except KeyError:
                    # If it's not imported, just bail, as we can't
                    # edit this field safely.
                    return None
            kwargs["reference_class"] = reference_class

        kwargs.setdefault("allow_blank", not prop._required)

        if prop._repeated:
            return RepeatedKeyPropertyField(**kwargs)
        else:
            return KeyPropertyField(**kwargs)

    def convert__ClassKeyProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.ComputedProperty``."""
        return None


def model_fields(model, only=None, exclude=None, field_args=None, converter=None):
    """
    Extracts and returns a dictionary of form fields for a given
    ``db.Model`` class.

    :param model:
        The ``db.Model`` class to extract fields from.
    :param only:
        An optional iterable with the property names that should be included in
        the form. Only these properties will have fields.
    :param exclude:
        An optional iterable with the property names that should be excluded
        from the form. All other properties will have fields.
    :param field_args:
        An optional dictionary of field names mapping to a keyword arguments
        used to construct each field object.
    :param converter:
        A converter to generate the fields based on the model properties. If
        not set, ``ModelConverter`` is used.
    """
    converter = converter or ModelConverter()
    field_args = field_args or {}

    # Get the field names we want to include or exclude, starting with the
    # full list of model properties.
    props = model._properties
    field_names = [
        x[0] for x in sorted(props.items(), key=lambda x: x[1]._creation_counter)
    ]

    if only:
        field_names = list(f for f in only if f in field_names)
    elif exclude:
        field_names = list(f for f in field_names if f not in exclude)

    # Create all fields.
    field_dict = {}
    for name in field_names:
        field = converter.convert(model, props[name], field_args.get(name))
        if field is not None:
            field_dict[name] = field

    return field_dict


def model_form(
    model,
    base_class=Form,
    only=None,
    exclude=None,
    field_args=None,
    converter=None,
    extra_fields=None,
):
    """
    Creates and returns a dynamic ``wtforms.Form`` class for a given
    ``ndb.Model`` class. The form class can be used as it is or serve as a base
    for extended form classes, which can then mix non-model related fields,
    subforms with other model forms, among other possibilities.

    :param model:
        The ``ndb.Model`` class to generate a form for.
    :param base_class:
        Base form class to extend from. Must be a ``wtforms.Form`` subclass.
    :param only:
        An optional iterable with the property names that should be included in
        the form. Only these properties will have fields.
    :param exclude:
        An optional iterable with the property names that should be excluded
        from the form. All other properties will have fields.
    :param field_args:
        An optional dictionary of field names mapping to keyword arguments
        used to construct each field object.
    :param converter:
        A converter to generate the fields based on the model properties. If
        not set, ``ModelConverter`` is used.
    """
    # Extract the fields from the model.
    field_dict = model_fields(model, only, exclude, field_args, converter)

    if extra_fields:
        field_dict.update(extra_fields)

    # Return a dynamically created form class, extending from base_class and
    # including the created fields as properties.
    return type(model._get_kind() + "Form", (base_class,), field_dict)
