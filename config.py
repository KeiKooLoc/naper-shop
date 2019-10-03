import os

conf = dict(
    TOKEN=os.environ.get("TELEGRAM_TOKEN") or "975543672:AAGctJ8L1-ZqCpm1J1jbgYAQZapYAN0H6o8",
    PRODUCTS_PER_PAGE=5,
    ORDERS_PER_PAGE=10,
    ADMINS=[321858998,  # Me
            # 500034808   # Dimon
            ]
)
