import math
from decimal import Decimal
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


def format_inr(number, decimals=0):
    """
    Format a number according to the Indian numbering system.
    e.g. 1299 -> 1,299
         149999 -> 1,49,999
         1234567 -> 12,34,567
    """
    if number is None or number == '':
        return '₹0'

    try:
        val = float(number)
    except (ValueError, TypeError):
        return f"₹{number}"

    is_negative = val < 0
    val = abs(val)

    if decimals > 0:
        formatted_str = f"{val:.{decimals}f}"
        parts = formatted_str.split('.')
        int_part = parts[0]
        dec_part = '.' + parts[1]
    else:
        int_part = str(int(round(val)))
        dec_part = ''

    if len(int_part) <= 3:
        grouped = int_part
    else:
        last3 = int_part[-3:]
        remaining = int_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        grouped = ','.join(groups) + ',' + last3

    sign = '-' if is_negative else ''
    return f"{sign}₹{grouped}{dec_part}"


@register.filter(name='rupee')
def rupee(value):
    """
    Template filter to display INR with symbol and Indian comma formatting.
    Usage: {{ product.selling_price|rupee }} -> ₹1,299
    """
    return format_inr(value, decimals=0)


@register.filter(name='rupee_dec')
def rupee_dec(value):
    """
    Template filter to display INR with 2 decimal places.
    Usage: {{ order.total_amount|rupee_dec }} -> ₹1,299.00
    """
    return format_inr(value, decimals=2)


@register.filter(name='discount_pct')
def discount_pct(product):
    """
    Calculates discount percentage between MRP and selling price.
    """
    if not product or not hasattr(product, 'mrp') or not hasattr(product, 'selling_price'):
        return 0
    if product.mrp and product.mrp > 0 and product.selling_price < product.mrp:
        pct = round(((product.mrp - product.selling_price) / product.mrp) * 100)
        return int(pct)
    return 0


@register.filter(name='star_range')
def star_range(rating):
    """
    Returns a list of full star count for visual rating rendering.
    """
    try:
        r = float(rating)
        full_stars = int(math.floor(r))
        return range(min(max(full_stars, 0), 5))
    except (ValueError, TypeError):
        return range(4)
