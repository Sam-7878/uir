"""Frozen monetary normalization: B/M/T scale, USD/KRW, otherwise base units."""
from decimal import Decimal, InvalidOperation
import re

SCALES = {'': Decimal(1), 'BASE': Decimal(1), 'B': Decimal('1e9'),
          'BILLION': Decimal('1e9'), 'M': Decimal('1e6'), 'MILLION': Decimal('1e6'),
          'T': Decimal('1e12'), 'TRILLION': Decimal('1e12')}
_PATTERN = re.compile(r'([$₩]?)\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*([BMT]?)\s*(USD|KRW)?', re.I)

def parse_quantity(value, currency='', unit=''):
    """Return an exact amount in base currency units, or None on conflicting units.

    Omitting a scale means base units, not the scale of the expected answer.
    Currency may be supplied by the frozen task context; a supplied conflicting
    symbol/code is always invalid. No unrelated text fields are searched.
    """
    match = _PATTERN.fullmatch(str(value).replace(',', '').strip())
    if not match:
        return None
    symbol, number, embedded_unit, embedded_currency = match.groups()
    codes = {str(x).upper() for x in (currency, embedded_currency, {'$':'USD','₩':'KRW'}.get(symbol)) if x}
    if len(codes) > 1:
        return None
    unit = str(unit).upper()
    if unit not in SCALES:
        return None
    if embedded_unit and unit and SCALES[embedded_unit.upper()] != SCALES[unit]:
        return None
    scale = SCALES[embedded_unit.upper() or unit]
    try:
        amount = Decimal(number) * scale
    except InvalidOperation:
        return None
    if not amount.is_finite():
        return None
    return amount, next(iter(codes), '')
