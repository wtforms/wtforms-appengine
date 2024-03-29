import operator

from wtforms import fields
from wtforms import widgets

__all__ = [
    "ReferencePropertyField",
    "StringListPropertyField",
    "IntegerListPropertyField",
]


class ReferencePropertyField(fields.SelectFieldBase):
    """
    A field for ``db.ReferenceProperty``. The list items are rendered in a
    select.

    :param reference_class:
        A db.Model class which will be used to generate the default query
        to make the list of items. If this is not specified, The `query`
        property must be overridden before validation.
    :param get_label:
        If a string, use this attribute on the model class as the label
        associated with each option. If a one-argument callable, this callable
        will be passed model instance and expected to return the label text.
        Otherwise, the model object's `__str__` or `__unicode__` will be used.
    :param allow_blank:
        If set to true, a blank choice will be added to the top of the list
        to allow `None` to be chosen.
    :param blank_text:
        Use this to override the default blank option's label.
    """

    widget = widgets.Select()

    def __init__(
        self,
        label=None,
        validators=None,
        reference_class=None,
        get_label=None,
        allow_blank=False,
        blank_text="",
        **kwargs
    ):
        super().__init__(label, validators, **kwargs)
        if get_label is None:
            self.get_label = lambda x: x
        elif isinstance(get_label, str):
            self.get_label = operator.attrgetter(get_label)
        else:
            self.get_label = get_label

        self.allow_blank = allow_blank
        self.blank_text = blank_text
        self._set_data(None)
        if reference_class is not None:
            self.query = reference_class.all()

    def _get_data(self):
        if self._formdata is not None:
            for obj in self.query:
                if str(obj.key()) == self._formdata:
                    self._set_data(obj)
                    break
        return self._data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)

    def iter_choices(self):
        if self.allow_blank:
            yield ("__None", self.blank_text, self.data is None)

        for obj in self.query:
            key = str(obj.key())
            label = self.get_label(obj)
            yield (key, label, (self.data.key() == obj.key()) if self.data else False)

    def process_formdata(self, valuelist):
        if valuelist:
            if valuelist[0] == "__None":
                self.data = None
            else:
                self._data = None
                self._formdata = valuelist[0]

    def pre_validate(self, form):
        data = self.data
        if data is not None:
            s_key = str(data.key())
            for obj in self.query:
                if s_key == str(obj.key()):
                    break
            else:
                raise ValueError(self.gettext("Not a valid choice"))
        elif not self.allow_blank:
            raise ValueError(self.gettext("Not a valid choice"))


class StringListPropertyField(fields.TextAreaField):
    """
    A field for ``db.StringListProperty``. The list items are rendered in a
    textarea.
    """

    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        else:
            return self.data and str("\n".join(self.data)) or ""

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = valuelist[0].splitlines()
            except ValueError as exc:
                raise ValueError(self.gettext("Not a valid list")) from exc


class IntegerListPropertyField(fields.TextAreaField):
    """
    A field for ``db.StringListProperty``. The list items are rendered in a
    textarea.
    """

    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        else:
            return str("\n".join(self.data)) if self.data else ""

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = [int(value) for value in valuelist[0].splitlines()]
            except ValueError as exc:
                raise ValueError(self.gettext("Not a valid integer list")) from exc
