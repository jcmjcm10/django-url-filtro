import coreapi
import coreschema
from django import forms
from django.db.models.constants import LOOKUP_SEP

from ..fields import MultipleValuesField
from ..filtersets import FilterSet
from .drf import URLFilterBackend


DESCRIPTION = {
    "contains": "Match when string contains given substring",
    "day": "Match by day of the month",
    "endswith": "Match when string ends with given substring",
    "exact": "Match exactly the value as is",
    "gt": "Match when value is greater then given value",
    "gte": "Match when value is greater or equal then given value",
    "hour": "Match by the hour (24 hour) value of the timestamp",
    "icontains": "Case insensitive match when string contains given substring",
    "iendswith": "Case insensitive match when string ends with given substring",
    "iexact": "Case insensitive match exactly the value as is",
    "iin": "Case insensitive match when value is any of given comma separated values",
    "in": "Match when value is any of given comma separated values",
    "iregex": "Case insensitive match string by regex pattern",
    "isnull": "Match when value is NULL",
    "istartswith": "Case insensitive match when string starts with given substring",
    "lt": "Match when value is less then given value",
    "lte": "Match when value is less or equal then given value",
    "minute": "Match by the minute value of the timestamp",
    "month": "Match by the month value of the timestamp",
    "range": "Match when value is within comma separated range",
    "regex": "Match string by regex pattern",
    "second": "Match by the second value of the timestamp",
    "startswith": "Match when string starts with given substring",
    "week_day": "Match by week day (1-Sunday to 7-Saturday) of the timestamp",
    "year": "Match by the year value of the timestamp",
}

FORM_FIELD_TO_SCHEMA = {
    MultipleValuesField: coreschema.Array,
    forms.BooleanField: coreschema.Boolean,
    forms.IntegerField: coreschema.Integer,
    forms.FloatField: coreschema.Number,
}


def _field_to_schema(field, lookup):
    form_field = field.get_form_field(lookup)
    return FORM_FIELD_TO_SCHEMA.get(type(form_field), coreschema.String)(
        description=DESCRIPTION.get(lookup)
    )


def _all_filters(filterset, prefix=()):
    for name, field in filterset.filters.items():
        if isinstance(field, FilterSet):
            for i in _all_filters(field, prefix=prefix + (name,)):
                yield i

        else:
            yield coreapi.Field(
                name=LOOKUP_SEP.join(prefix + (name,)),
                required=False,
                location="query",
                schema=_field_to_schema(field, field.default_lookup),
            )
            if field.no_lookup:
                continue
            for lookup in field.lookups:
                yield coreapi.Field(
                    name=LOOKUP_SEP.join(prefix + (name, lookup)),
                    required=False,
                    location="query",
                    schema=_field_to_schema(field, lookup),
                )


class CoreAPIURLFilterBackend(URLFilterBackend):
    """
    Same as :py:class:`url_filter.integrations.drf.DjangoFilterBackend` except
    this backend also implements coreapi interface for autogenerated API docs.
    """

    def get_schema_fields(self, view):
        """
        Get coreapi filter definitions

        Returns all filters including their supported lookups.
        """
        queryset = view.get_queryset()
        filter_class = self.get_filter_class(view, queryset)

        return (
            []
            if not filter_class
            else list(_all_filters(filter_class(data={}, queryset=queryset)))
        )
