"""PayPal wire minor digits, which differ from ISO for HUF and TWD."""

# Verified 2026-11-02: https://developer.paypal.com/api/codes/currency/
# That page explicitly lists RUB; availability remains account/product dependent.
# HUF, JPY, TWD have footnote 1: no decimals. All codes below confirmed there.
CURRENCY_MINOR_DIGITS: dict[str, int] = {
    "AUD": 2,
    "BRL": 2,
    "CAD": 2,
    "CNY": 2,
    "CZK": 2,
    "DKK": 2,
    "EUR": 2,
    "GBP": 2,
    "HKD": 2,
    "HUF": 0,
    "ILS": 2,
    "JPY": 0,
    "MXN": 2,
    "MYR": 2,
    "NOK": 2,
    "NZD": 2,
    "PHP": 2,
    "PLN": 2,
    "RUB": 2,
    "SEK": 2,
    "SGD": 2,
    "CHF": 2,
    "THB": 2,
    "TWD": 0,
    "USD": 2,
}
PAYPAL_ZERO_DECIMAL = frozenset({"HUF", "JPY", "TWD"})
UNCONFIRMED_CURRENCIES: frozenset[str] = frozenset()
