import decimal

from wtforms import fields

from .db import *
from .ndb import *


class GeoPtPropertyField(fields.StringField):
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                lat, lon = valuelist[0].split(",")
                self.data = "{},{}".format(
                    decimal.Decimal(lat.strip()), decimal.Decimal(lon.strip())
                )

            except (decimal.InvalidOperation, ValueError) as exc:
                raise ValueError("Not a valid coordinate location") from exc
