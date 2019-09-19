from telegram.ext import Updater
import logging
from config import conf
from main import START_HANDLER, SHOP_HANDLER, ADMIN_START_HANDLER, ADD_PRODUCT_HANDLER, BACK_TO_USER_MENU, \
    USER_ORDERS_HANDLER, ADMIN_ORDERS_HANDLER, CONTACTS_HANDLER, ADMIN_PRODUCTS_HANDLER


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    updater = Updater(conf["TOKEN"], use_context=True)
    dp = updater.dispatcher

    # USER SIDE
    dp.add_handler(START_HANDLER)
    dp.add_handler(CONTACTS_HANDLER)
    dp.add_handler(SHOP_HANDLER)
    dp.add_handler(USER_ORDERS_HANDLER)

    # ADMIN SIDE
    dp.add_handler(ADMIN_START_HANDLER)
    dp.add_handler(ADD_PRODUCT_HANDLER)
    dp.add_handler(BACK_TO_USER_MENU)
    dp.add_handler(ADMIN_ORDERS_HANDLER)
    dp.add_handler(ADMIN_PRODUCTS_HANDLER)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)