#!/usr/bin/env python
"""
Unittests for wtforms_appengine

To run the tests, use NoseGAE:

pip install nose nosegae

nosetests --with-gae --without-sandbox
"""
# This needs to stay as the first import, it sets up paths.
from unittest import TestCase
from wtforms_appengine.db import model_form
from wtforms_appengine.fields import GeoPtPropertyField
from wtforms_appengine.fields import ReferencePropertyField
from wtforms_appengine.fields import StringListPropertyField

from google.appengine.ext import db
from wtforms import fields as f
from wtforms import Form
from wtforms import validators

from .gaetest_common import DBTestCase
from .gaetest_common import DummyPostData
from .gaetest_common import fill_authors


class Author(db.Model):
    name = db.StringProperty(required=True)
    city = db.StringProperty()
    age = db.IntegerProperty(required=True)
    is_admin = db.BooleanProperty(default=False)


class Book(db.Model):
    author = db.ReferenceProperty(Author)


class AllPropertiesModel(db.Model):
    """Property names are ugly, yes."""

    prop_string = db.StringProperty()
    prop_byte_string = db.ByteStringProperty()
    prop_boolean = db.BooleanProperty()
    prop_integer = db.IntegerProperty()
    prop_float = db.FloatProperty()
    prop_date_time = db.DateTimeProperty()
    prop_date = db.DateProperty()
    prop_time = db.TimeProperty()
    prop_list = db.ListProperty(int)
    prop_string_list = db.StringListProperty()
    prop_reference = db.ReferenceProperty()
    prop_self_refeference = db.SelfReferenceProperty()
    prop_user = db.UserProperty()
    prop_blob = db.BlobProperty()
    prop_text = db.TextProperty()
    prop_category = db.CategoryProperty()
    prop_link = db.LinkProperty()
    prop_email = db.EmailProperty()
    prop_geo_pt = db.GeoPtProperty()
    prop_im = db.IMProperty()
    prop_phone_number = db.PhoneNumberProperty()
    prop_postal_address = db.PostalAddressProperty()
    prop_rating = db.RatingProperty()


class DateTimeModel(db.Model):
    prop_date_time_1 = db.DateTimeProperty()
    prop_date_time_2 = db.DateTimeProperty(auto_now=True)
    prop_date_time_3 = db.DateTimeProperty(auto_now_add=True)

    prop_date_1 = db.DateProperty()
    prop_date_2 = db.DateProperty(auto_now=True)
    prop_date_3 = db.DateProperty(auto_now_add=True)

    prop_time_1 = db.TimeProperty()
    prop_time_2 = db.TimeProperty(auto_now=True)
    prop_time_3 = db.TimeProperty(auto_now_add=True)


class TestModelForm(DBTestCase):
    nosegae_datastore_v3 = True

    def test_model_form_basic(self):
        form_class = model_form(Author)

        self.assertEqual(hasattr(form_class, "name"), True)
        self.assertEqual(hasattr(form_class, "age"), True)
        self.assertEqual(hasattr(form_class, "city"), True)
        self.assertEqual(hasattr(form_class, "is_admin"), True)

        form = form_class()
        self.assertEqual(isinstance(form.name, f.StringField), True)
        self.assertEqual(isinstance(form.city, f.StringField), True)
        self.assertEqual(isinstance(form.age, f.IntegerField), True)
        self.assertEqual(isinstance(form.is_admin, f.BooleanField), True)

    def test_required_field(self):
        form_class = model_form(Author)

        form = form_class()
        self.assertEqual(form.name.flags.required, True)
        self.assertEqual(form.city.flags.required, False)
        self.assertEqual(form.age.flags.required, True)
        self.assertEqual(form.is_admin.flags.required, False)

    def test_default_value(self):
        form_class = model_form(Author)

        form = form_class()
        self.assertEqual(form.name.default, None)
        self.assertEqual(form.city.default, None)
        self.assertEqual(form.age.default, None)
        self.assertEqual(form.is_admin.default, False)

    def test_model_form_only(self):
        form_class = model_form(Author, only=["name", "age"])

        self.assertEqual(hasattr(form_class, "name"), True)
        self.assertEqual(hasattr(form_class, "city"), False)
        self.assertEqual(hasattr(form_class, "age"), True)
        self.assertEqual(hasattr(form_class, "is_admin"), False)

        form = form_class()
        self.assertEqual(isinstance(form.name, f.StringField), True)
        self.assertEqual(isinstance(form.age, f.IntegerField), True)

    def test_model_form_exclude(self):
        form_class = model_form(Author, exclude=["is_admin"])

        self.assertEqual(hasattr(form_class, "name"), True)
        self.assertEqual(hasattr(form_class, "city"), True)
        self.assertEqual(hasattr(form_class, "age"), True)
        self.assertEqual(hasattr(form_class, "is_admin"), False)

        form = form_class()
        self.assertEqual(isinstance(form.name, f.StringField), True)
        self.assertEqual(isinstance(form.city, f.StringField), True)
        self.assertEqual(isinstance(form.age, f.IntegerField), True)

    def test_datetime_model(self):
        """Fields marked as auto_add / auto_add_now should not be included."""
        form_class = model_form(DateTimeModel)

        self.assertEqual(hasattr(form_class, "prop_date_time_1"), True)
        self.assertEqual(hasattr(form_class, "prop_date_time_2"), False)
        self.assertEqual(hasattr(form_class, "prop_date_time_3"), False)

        self.assertEqual(hasattr(form_class, "prop_date_1"), True)
        self.assertEqual(hasattr(form_class, "prop_date_2"), False)
        self.assertEqual(hasattr(form_class, "prop_date_3"), False)

        self.assertEqual(hasattr(form_class, "prop_time_1"), True)
        self.assertEqual(hasattr(form_class, "prop_time_2"), False)
        self.assertEqual(hasattr(form_class, "prop_time_3"), False)

    def test_not_implemented_properties(self):
        # This should not raise NotImplementedError.
        form_class = model_form(AllPropertiesModel)

        # These should be set.
        self.assertEqual(hasattr(form_class, "prop_string"), True)
        self.assertEqual(hasattr(form_class, "prop_byte_string"), True)
        self.assertEqual(hasattr(form_class, "prop_boolean"), True)
        self.assertEqual(hasattr(form_class, "prop_integer"), True)
        self.assertEqual(hasattr(form_class, "prop_float"), True)
        self.assertEqual(hasattr(form_class, "prop_date_time"), True)
        self.assertEqual(hasattr(form_class, "prop_date"), True)
        self.assertEqual(hasattr(form_class, "prop_time"), True)
        self.assertEqual(hasattr(form_class, "prop_string_list"), True)
        self.assertEqual(hasattr(form_class, "prop_reference"), True)
        self.assertEqual(hasattr(form_class, "prop_self_refeference"), True)
        self.assertEqual(hasattr(form_class, "prop_blob"), True)
        self.assertEqual(hasattr(form_class, "prop_text"), True)
        self.assertEqual(hasattr(form_class, "prop_category"), True)
        self.assertEqual(hasattr(form_class, "prop_link"), True)
        self.assertEqual(hasattr(form_class, "prop_email"), True)
        self.assertEqual(hasattr(form_class, "prop_geo_pt"), True)
        self.assertEqual(hasattr(form_class, "prop_phone_number"), True)
        self.assertEqual(hasattr(form_class, "prop_postal_address"), True)
        self.assertEqual(hasattr(form_class, "prop_rating"), True)

        # These should NOT be set.
        self.assertEqual(hasattr(form_class, "prop_list"), False)
        self.assertEqual(hasattr(form_class, "prop_user"), False)
        self.assertEqual(hasattr(form_class, "prop_im"), False)

    def test_populate_form(self):
        entity = Author(
            key_name="test", name="John", city="Yukon", age=25, is_admin=True
        )
        entity.put()

        obj = Author.get_by_key_name("test")
        form_class = model_form(Author)

        form = form_class(obj=obj)
        self.assertEqual(form.name.data, "John")
        self.assertEqual(form.city.data, "Yukon")
        self.assertEqual(form.age.data, 25)
        self.assertEqual(form.is_admin.data, True)

    def test_field_attributes(self):
        form_class = model_form(
            Author,
            field_args={
                "name": {
                    "label": "Full name",
                    "description": "Your name",
                },
                "age": {
                    "label": "Age",
                    "validators": [validators.NumberRange(min=14, max=99)],
                },
                "city": {
                    "label": "City",
                    "description": "The city in which you live, not the one in"
                    " which you were born.",
                },
                "is_admin": {
                    "label": "Administrative rights",
                },
            },
        )
        form = form_class()

        self.assertEqual(form.name.label.text, "Full name")
        self.assertEqual(form.name.description, "Your name")

        self.assertEqual(form.age.label.text, "Age")

        self.assertEqual(form.city.label.text, "City")
        self.assertEqual(
            form.city.description,
            "The city in which you live, not the one in which you were born.",
        )

        self.assertEqual(form.is_admin.label.text, "Administrative rights")

    def test_reference_property(self):
        keys = {"__None"}
        for name in ["foo", "bar", "baz"]:
            author = Author(name=name, age=26)
            author.put()
            keys.add(str(author.key()))

        form_class = model_form(Book)
        form = form_class()

        for key, _, _ in form.author.iter_choices():
            assert key in keys
            keys.remove(key)

        assert not keys


class TestGeoFields(TestCase):
    class GeoTestForm(Form):
        geo = GeoPtPropertyField()

    def test_geopt_property(self):
        form = self.GeoTestForm(DummyPostData(geo="5.0, -7.0"))
        self.assertTrue(form.validate())
        self.assertEqual(form.geo.data, "5.0,-7.0")
        form = self.GeoTestForm(DummyPostData(geo="5.0,-f"))
        self.assertFalse(form.validate())


class TestReferencePropertyField(DBTestCase):
    nosegae_datastore_v3 = True

    def build_form(self, reference_class=Author, **kw):
        class BookForm(Form):
            author = ReferencePropertyField(reference_class=reference_class, **kw)

        return BookForm

    def author_expected(self, selected_index, get_label=lambda x: x.name):
        expected = set()
        for i, author in enumerate(self.authors):
            expected.add((str(author.key()), get_label(author), i == selected_index))
        return expected

    def setUp(self):
        super().setUp()

        self.authors = fill_authors(Author)
        self.author_names = {x.name for x in self.authors}
        self.author_ages = {x.age for x in self.authors}

    def test_basic(self):
        F = self.build_form(get_label="name")
        form = F()
        self.assertEqual(set(form.author.iter_choices()), self.author_expected(None))
        assert not form.validate()

        form = F(DummyPostData(author=str(self.authors[0].key())))
        assert form.validate()
        self.assertEqual(set(form.author.iter_choices()), self.author_expected(0))

    def test_not_in_query(self):
        F = self.build_form()
        new_author = Author(name="Jim", age=48)
        new_author.put()
        form = F(author=new_author)
        form.author.query = Author.all().filter("name !=", "Jim")
        assert form.author.data is new_author
        assert not form.validate()

    def test_get_label_func(self):
        def get_age(x):
            return x.age

        F = self.build_form(get_label=get_age)
        form = F()
        ages = {x.label.text for x in form.author}
        self.assertEqual(ages, self.author_ages)

    def test_allow_blank(self):
        F = self.build_form(allow_blank=True, get_label="name")
        form = F(DummyPostData(author="__None"))
        assert form.validate()
        self.assertEqual(form.author.data, None)
        expected = self.author_expected(None)
        expected.add(("__None", "", True))
        self.assertEqual(set(form.author.iter_choices()), expected)


class TestStringListPropertyField(TestCase):
    class F(Form):
        a = StringListPropertyField()

    def test_basic(self):
        form = self.F(DummyPostData(a="foo\nbar\nbaz"))
        self.assertEqual(form.a.data, ["foo", "bar", "baz"])
        self.assertEqual(form.a._value(), "foo\nbar\nbaz")
