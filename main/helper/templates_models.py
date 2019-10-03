from telegram.error import TelegramError
from strings import strings
from db import products_table, orders_table
from config import conf
from bson import ObjectId
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode


class Order(object):
    def __init__(self, mode, _id=None, order_dict=None, ):
        """
        One of this filed required
        :param _id:        mongo _id of order document
        :param order_dict: dict with order data
        """
        if _id:
            if type(_id) == str:
                _id = ObjectId(_id)
            self.order = orders_table.find_one(
                {"_id": _id})
            # self.deleted = True if self.order else False
        if order_dict:
            self.order = order_dict
            # self.order = orders_table.find_one(
            #     {"_id": order_dict["_id"]})
        # self.deleted = True if self.order else False

    """def pass_if_not_found(self, func):
        def wrapper(self=self, *args, **kwargs):
            if self.deleted:
                return "Deleted"
            else:
                func(*args, **kwargs)
        return wrapper"""

    """ADMIN METHODS"""
    def send_short_template(self, update, context):
        kb = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(strings["select_order_btn"],
                                           callback_data=f"select_order/{self.order['_id']}")]])
        context.user_data["to_delete"].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["short_order_template"].format(
                                         self.order["user_mention_markdown"],
                                         str(self.order['creation_timestamp']).split('.')[0]),
                                     reply_markup=kb,
                                     parse_mode=ParseMode.MARKDOWN))

    def admin_template(self, order, product):
        # user_status = "🚫Удалён" if order["deleted_on_user_side"] else "⚠ В ожидании ️"
        # extra_string = "\n_Юзер отменил заказ. Можете смело удалять запись_" \
        #     if order["deleted_on_user_side"] else ""
        user_status = "⛔ ️🚫Продан" if order["status"] else "⚠ В ожидании ️"
        return Product().template(product) + \
               strings["admin_order_template"].format(
                   order["user_mention_markdown"],
                   str(order['creation_timestamp']).split('.')[0],
                   user_status)

    def send_admin_template(self, update, context, order_id, extra_str="", kb=None):
        if type(order_id) == str:
            order_id = ObjectId(order_id)
        order = orders_table.find_one({"_id": order_id})
        # if not order:
        #     return False
        product = products_table.find_one({"_id": order["product_id"]})
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   product["image_id"],
                                   self.admin_template(order, product) + extra_str,
                                   reply_markup=kb,
                                   parse_mode=ParseMode.MARKDOWN))

    """USER METHODS"""
    def send_user_template(self, update, context, kb=None):
        order_status = "😘 Продан Вам" if self.order["status"] else "⚠ В ожидании ️"
        product = products_table.find_one({"_id": self.order["product_id"]})
        if not product:
            context.user_data["to_delete"].append(

            )
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   product["image_id"],
                                   Product().template(product) +
                                   strings["order_template"].format(
                                       str(self.order['creation_timestamp']).split('.')[0],
                                       order_status),
                                   reply_markup=kb,
                                   parse_mode=ParseMode.MARKDOWN))


class Product(object):
    def template(self, product):
        if product:
            if product.get("_id"):
                if product["sold"]:
                    product_status = "Продан⛔ ️"
                else:
                    product_status = "В наличии ✅"

                return strings["product_template_2"].format(
                    product["name"], product["price"], product["description"], product_status)

            return strings["product_template"].format(
                product["name"], product["price"], product["description"])
        else:
            return "Товар удалён из магазина"
