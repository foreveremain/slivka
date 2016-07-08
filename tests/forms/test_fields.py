import os
import tempfile
import unittest

from pybioas.server.forms import ValidationError
from pybioas.server.forms.fields import (
    BaseField, IntegerField, DecimalField, FileField,
    TextField, BooleanField, ChoiceField
)
from pybioas.utils import Bunch


class TestBaseFieldValid(unittest.TestCase):
    def test_type(self):
        field = BaseField('')
        self.assertEqual(field.type, "base")

    def test_default(self):
        field = BaseField('', default='foo')
        self.assertEqual(field.default, 'foo')
        with self.assertRaises(AttributeError):
            # noinspection PyPropertyAccess
            field.default = 'bar'
        self.assertEqual(field.value, 'foo')

    def test_required(self):
        field = BaseField('', required=True)
        with self.assertRaises(ValidationError) as cm:
            field.validate(None)
        self.assertEqual(cm.exception.code, 'required')
        with self.assertRaises(ValidationError) as cm:
            # noinspection PyStatementEffect
            field.cleaned_value
        self.assertEqual(cm.exception.code, 'required')
        self.assertFalse(field.is_valid)
        field.value = 'foo'
        self.assertTrue(field.is_valid)

    def test_not_required(self):
        field = BaseField('', required=False)
        self.assertTrue(field.is_valid)

    def test_value(self):
        field = BaseField('', default="foo")
        self.assertEqual(field.value, "foo")
        field.value = 'bar'
        self.assertEqual(field.value, 'bar')

    def test_invalidation(self):
        field = BaseField('', default='foo')
        field._valid = True
        self.assertTrue(field.is_valid)
        field.value = 'bar'
        self.assertFalse(field._valid)

    def test_error(self):
        field = BaseField('')
        self.assertIsNone(field.error)


class TestIntegerField(unittest.TestCase):
    def test_is_valid_int(self):
        field = IntegerField('')
        field.value = 10
        self.assertTrue(field.is_valid)
        field.value = "10"
        self.assertTrue(field.is_valid)
        field.value = "3.5"
        self.assertFalse(field.is_valid)
        field.value = "-4"
        self.assertTrue(field.is_valid)

    def test_required(self):
        field = IntegerField('', required=True)
        with self.assertRaises(ValidationError) as cm:
            field.validate(None)
        self.assertEqual(cm.exception.code, 'required')

    def test_is_valid_min(self):
        field = IntegerField('', minimum=-10)
        field.value = -10
        self.assertTrue(field.is_valid)
        field.value = -11
        self.assertFalse(field.is_valid)

    def test_is_valid_max(self):
        field = IntegerField('', maximum=20)
        field.value = 20
        self.assertTrue(field.is_valid)
        field.value = 21
        self.assertFalse(field.is_valid)

    def test_cleaned_data(self):
        field = IntegerField('', default=4)
        self.assertEqual(field.cleaned_value, 4)
        field.value = "True"
        with self.assertRaises(ValidationError):
            # noinspection PyStatementEffect
            field.cleaned_value
        field.value = '10'
        self.assertEqual(field.cleaned_value, 10)


class TestDecimalField(unittest.TestCase):
    def test_is_valid_decimal(self):
        field = DecimalField('')
        field.value = 3.1415
        self.assertTrue(field.is_valid)
        field.value = "3.5"
        self.assertTrue(field.is_valid)
        field.value = "abc"
        self.assertFalse(field.is_valid)
        field.value = "-2.71"
        self.assertTrue(field.is_valid)

    def test_required(self):
        field = DecimalField('', required=True)
        with self.assertRaises(ValidationError) as cm:
            field.validate(None)
        self.assertEqual(cm.exception.code, 'required')

    def test_cleaned_data(self):
        field = DecimalField('')
        field.value = 3.1415
        self.assertAlmostEqual(field.cleaned_value, 3.1415)
        field.value = "foobar"
        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            field.cleaned_value
        field.value = "0.12345678987654321"
        self.assertAlmostEqual(field.cleaned_value, 0.12345678)

    def test_is_valid_min_inclusive(self):
        field = DecimalField('', minimum=5, min_exclusive=False)
        field.value = 5
        self.assertTrue(field.is_valid)
        field.value = 4.99
        self.assertFalse(field.is_valid)

    def test_is_valid_min_exclusive(self):
        field = DecimalField('', minimum=5, min_exclusive=True)
        field.value = 5
        self.assertFalse(field.is_valid)
        field.value = 4.99
        self.assertFalse(field.is_valid)
        field.value = 5.01
        self.assertTrue(field.is_valid)

    def test_is_valid_max_inclusive(self):
        field = DecimalField('', maximum=5, max_exclusive=False)
        field.value = 5
        self.assertTrue(field.is_valid)
        field.value = 5.01
        self.assertFalse(field.is_valid)

    def test_is_valid_exclusive(self):
        field = DecimalField('', maximum=5, max_exclusive=True)
        field.value = 5
        self.assertFalse(field.is_valid)
        field.value = 5.01
        self.assertFalse(field.is_valid)
        field.value = 4.99
        self.assertTrue(field.is_valid)


class TestFileField(unittest.TestCase):
    temp_dir = None

    @classmethod
    def setUpClass(cls):
        import pybioas.config
        from pybioas.db import models, start_session, create_db

        cls.temp_dir = tempfile.TemporaryDirectory()
        settings = Bunch(
            BASE_DIR=cls.temp_dir.name,
            MEDIA_DIR=".",
            SECRET_KEY=b'\x00',
            SERVICE_INI=None
        )
        with open(os.path.join(cls.temp_dir.name, "foo"), "w") as f:
            f.write("bar bar")
        pybioas.settings = pybioas.config.Settings(settings)
        create_db()
        with start_session() as session:
            file = models.File(id="foo")
            session.add(file)
            session.commit()

    def test_required(self):
        field = FileField('', required=True)
        with self.assertRaises(ValidationError) as cm:
            field.validate(None)
        self.assertEqual(cm.exception.code, 'required')

    def test_file_not_exist(self):
        field = FileField('')
        field.value = "bar"
        self.assertFalse(field.is_valid)

    def test_file_exists(self):
        field = FileField('')
        field.value = "foo"
        self.assertTrue(field.is_valid)

    def test_file_path(self):
        field = FileField('')
        cleaned = field.validate("foo")
        self.assertEqual(
            os.path.dirname(cleaned), self.temp_dir.name
        )
        self.assertEqual(
            os.path.basename(cleaned), "foo"
        )

    @classmethod
    def tearDownClass(cls):
        from pybioas.db import drop_db

        drop_db()
        cls.temp_dir.cleanup()


class TestTextField(unittest.TestCase):
    def test_is_valid(self):
        field = TextField('')
        field.value = "abc"
        self.assertTrue(field.is_valid)
        field.value = 123
        self.assertTrue(field.is_valid)

    def test_required(self):
        field = TextField('', required=True)
        with self.assertRaises(ValidationError) as cm:
            field.validate(None)
        self.assertEqual(cm.exception.code, 'required')

    def test_cleaned_value(self):
        field = TextField('')
        field.value = "abc"
        self.assertEqual(field.cleaned_value, "abc")
        field.value = 123
        self.assertEqual(field.cleaned_value, "123")

    def test_is_valid_max_length(self):
        field = TextField('', max_length=10)
        field.value = "some very long message goes here"
        self.assertFalse(field.is_valid)
        field.value = "short text"
        self.assertTrue(field.is_valid)

    def test_is_valid_min_length(self):
        field = TextField('', min_length=10)
        field.value = "tiny"
        self.assertFalse(field.is_valid)
        field.value = "short text"
        self.assertTrue(field.is_valid)


class TestBooleanField(unittest.TestCase):
    def setUp(self):
        self.field = BooleanField('', required=True)

    def test_is_valid(self):
        self.field.value = True
        self.assertTrue(self.field.is_valid)
        self.field.value = "yes"
        self.assertTrue(self.field.is_valid)
        self.field.value = 0
        self.assertTrue(self.field.is_valid)
        self.field.value = False
        self.assertTrue(self.field.is_valid)

    def test_required(self):
        with self.assertRaises(ValidationError) as cm:
            self.field.validate(None)
        self.assertEqual(cm.exception.code, 'required')

    def test_cleaned_data_true(self):
        for value in [1, True, 'yes', 'true', 'TRUE', 'True', 'LOL', '1',
                      object(), type('', (), {})]:
            self.field.value = value
            self.assertEqual(
                self.field.cleaned_value, True,
                "invalid value for %s" % value
            )

    def test_cleaned_data_false(self):
        for value in [0, False, 'no', 'false', 'FALSE', 'False', '0', ()]:
            self.field.value = value
            self.assertEqual(
                self.field.cleaned_value, False,
                "invalid value for %r" % (value,)
            )


class TestSelectField(unittest.TestCase):
    def setUp(self):
        self.field = ChoiceField('', choices=("alpha", "beta", "gamma"))

    def test_is_valid(self):
        self.field.value = "alpha"
        self.assertTrue(self.field.is_valid)
        self.field.value = "beta"
        self.assertTrue(self.field.is_valid)
        self.field.value = "gamma"
        self.assertTrue(self.field.is_valid)
        self.field.value = "delta"
        self.assertFalse(self.field.is_valid)

    def test_required(self):
        with self.assertRaises(ValidationError) as cm:
            self.field.validate(None)
        self.assertEqual(cm.exception.code, 'required')

    def test_not_required(self):
        field = ChoiceField('', required=False, choices=('a', 'b'))
        self.assertIsNone(field.cleaned_value)

    def test_cleaned_data(self):
        self.field.value = "gamma"
        self.assertEqual(self.field.cleaned_value, "gamma")
