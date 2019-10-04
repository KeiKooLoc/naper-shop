from bson import ObjectId
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from config import conf
from .strings import strings
from db import products_table, orders_table


class Order(object):
    def __init__(self, _id=None, order_dict=None):
        """
        One of this filed required
        :param _id:        mongo _id of order document
        :param order_dict: dict with order data
        """
        if _id:
            if type(_id) == str:
                _id = ObjectId(_id)
            self.order = orders_table.find_one({"_id": _id})
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

    """def admin_template(self, order, product):
        user_status = "⛔ ️🚫Продан" if order["status"] else "⚠ В ожидании ️"
        return Product(product_dict=product).template() + \
               strings["admin_order_template"].format(
                   order["user_mention_markdown"],
                   str(order['creation_timestamp']).split('.')[0],
                   user_status)"""

    def send_admin_template(self, update, context, extra_str="", kb=None):
        order_status = "⛔ ️🚫Продан" if self.order["status"] else "⚠ В ожидании ️"
        p = Product(_id=self.order["product_id"])
        if not p.product:
            p = Product(product_dict=self.order["product_object"])
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   p.product["image_id"],
                                   p.template() +
                                   strings["admin_order_template"].format(
                                       self.order["user_mention_markdown"],
                                       str(self.order['creation_timestamp']).split('.')[0],
                                       order_status) + extra_str,
                                   reply_markup=kb,
                                   parse_mode=ParseMode.MARKDOWN))

    def new_order_notification(self, context):
        order_status = "⛔ ️🚫Продан" if self.order["status"] else "⚠ В ожидании ️"
        p = Product(_id=self.order["product_id"])
        for chat_id in conf["ADMINS"]:
            context.bot.send_photo(chat_id,
                                   p.product["image_id"],
                                   p.template() +
                                   strings["admin_order_template"].format(
                                       self.order["user_mention_markdown"],
                                       str(self.order['creation_timestamp']).split('.')[0],
                                       order_status) + strings["new_order_notification"],
                                   parse_mode=ParseMode.MARKDOWN)

    """USER METHODS"""
    def send_user_template(self, update, context, extra_str="", kb=None):
        order_status = "😘 Продан Вам" if self.order["status"] else "⚠ В ожидании ️"
        product = products_table.find_one({"_id": self.order["product_id"]})
        if not product and self.order["status"]:
            product = self.order["product_object"]
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   product["image_id"],
                                   Product(product_dict=product).template() +
                                   strings["order_template"].format(
                                       str(self.order['creation_timestamp']).split('.')[0],
                                       order_status) + extra_str,
                                   reply_markup=kb,
                                   parse_mode=ParseMode.MARKDOWN))


class Product(object):
    def __init__(self, _id=None, product_dict=None):
        """
        One of this filed required
        :param _id:        mongo _id of product document
        :param order_dict: dict with product data
        """
        if _id:
            if type(_id) == str:
                _id = ObjectId(_id)
            self.product = products_table.find_one({"_id": _id})
            if not self.product:
                self.deleted = True
        if product_dict:
            self.product = product_dict

    def template(self):
        if self.product:
            if self.product.get("_id"):
                product_status = "Продан⛔ ️" if self.product["sold"] else "В наличии ✅"
                return strings["product_template_2"].format(
                    self.product["name"], self.product["price"],
                    self.product["description"], product_status)
            return strings["product_template"].format(
                self.product["name"], self.product["price"], self.product["description"])
        else:
            return "Товар удалён из магазина"

    def send_product_template(self, update, context, extra_str="", kb=None):
        context.user_data['to_delete'].append(
            context.bot.send_photo(update.effective_chat.id,
                                   self.product["image_id"],
                                   self.template() + extra_str,
                                   reply_markup=kb,
                                   parse_mode=ParseMode.MARKDOWN))

    def new_product_notification(self, context):
        for chat_id in conf["ADMINS"]:
            context.bot.send_photo(chat_id,
                                   self.product["image_id"],
                                   self.template() + f"\n\n{strings['success_adding']}",
                                   parse_mode=ParseMode.MARKDOWN)
