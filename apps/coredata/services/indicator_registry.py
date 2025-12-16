from typing import Iterable

from apps.coredata.models import Indicator


def get_input_indicators() -> Iterable[Indicator]:
    return Indicator.objects.filter(type=Indicator.INPUT)


def get_computed_indicators() -> Iterable[Indicator]:
    return Indicator.objects.filter(type=Indicator.COMPUTED)
