import unittest
from decimal import Decimal

from order_totals import order_total


class OrderTotalTests(unittest.TestCase):
    def test_regular_order_without_coupon(self):
        total = order_total(
            [(Decimal("10.00"), 2)],
            Decimal("0"),
            Decimal("0.05"),
            Decimal("100.00"),
        )
        self.assertEqual(total, Decimal("28.50"))

    def test_order_above_free_shipping_threshold(self):
        total = order_total(
            [(Decimal("60.00"), 2)],
            Decimal("0"),
            Decimal("0.05"),
            Decimal("100.00"),
        )
        self.assertEqual(total, Decimal("126.00"))


if __name__ == "__main__":
    unittest.main()
