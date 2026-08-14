from decimal import Decimal, ROUND_HALF_UP


SHIPPING_CHARGE = Decimal("7.50")
CENT = Decimal("0.01")


def order_total(lines, coupon_rate, tax_rate, free_shipping_threshold):
    if any(quantity <= 0 or int(quantity) != quantity for _, quantity in lines):
        raise ValueError("quantities must be positive integers")

    subtotal = sum((unit_price * quantity for unit_price, quantity in lines), Decimal("0"))
    discounted = subtotal * (Decimal("1") - coupon_rate)
    tax = discounted * tax_rate
    shipping = Decimal("0") if discounted >= free_shipping_threshold else SHIPPING_CHARGE
    return (discounted + tax + shipping).quantize(CENT, rounding=ROUND_HALF_UP)
