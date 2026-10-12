import frappe
from frappe.utils import flt, getdate, nowdate


@frappe.whitelist()
def get_exchange_rate(from_currency, to_currency, transaction_date=None, args=None):
	"""Return the rate for 1 `from_currency` in `to_currency`.

	Reads the latest `Currency Exchange` record dated on or before `transaction_date`
	(falls back to the latest record of any date). A record stored in the opposite
	direction is inverted. Returns 1.0 for identical currencies.
	"""
	if not from_currency or not to_currency:
		return 0.0
	if from_currency == to_currency:
		return 1.0

	transaction_date = getdate(transaction_date or nowdate())

	for date_filter in (["<=", transaction_date], None):
		for src, dst, invert in ((from_currency, to_currency, False), (to_currency, from_currency, True)):
			filters = {"from_currency": src, "to_currency": dst}
			if date_filter:
				filters["date"] = date_filter
			rate = frappe.db.get_value(
				"Currency Exchange", filters, "exchange_rate", order_by="date desc"
			)
			if flt(rate):
				return flt(1 / flt(rate), 9) if invert else flt(rate, 9)

	frappe.throw(
		frappe._("Unable to find exchange rate for {0} to {1}. Please add a Currency Exchange record.").format(
			from_currency, to_currency
		)
	)
