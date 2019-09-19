import os

conf = dict(
    TOKEN=os.environ.get("TELEGRAM_TOKEN"),
    PRODUCTS_PER_PAGE=5,
    ORDERS_PER_PAGE=10
)
