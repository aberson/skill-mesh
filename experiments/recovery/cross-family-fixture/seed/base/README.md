# Order total rules

`order_total` calculates one final customer charge.

- `REQ-QUANTITY`: Every quantity must be a positive integer. Reject zero or negative quantities with `ValueError`.
- `REQ-TAX`: Apply the coupon to merchandise before calculating tax.
- `REQ-SHIPPING`: Give free shipping when the discounted merchandise total is greater than or equal to the threshold.
- `REQ-ROUND`: Round the final total once, to two decimal places, with `ROUND_HALF_UP`.

Review the candidate against these rules and the changed code. Do not assume the public tests cover every boundary.
