from telegram.error import TelegramError
from strings import strings
from db import products_table, orders_table
from config import conf
from bson import ObjectId
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode


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
    # @pass_if_not_found
    def send_short_order(self, update, context):
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

    def send_admin_order_template(self, update, context, order_id, extra_str="", kb=None):
        if type(order_id) == str:
            order_id = ObjectId(order_id)
        order = orders_table.find_one({"_id": order_id})
        # if not order:
        #     return False
        product = products_table.find_one({"_id": order["product_id"]})
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   product["image_id"],
                                   admin_order_template(order, product) + extra_str,
                                   reply_markup=kb,
                                   parse_mode=ParseMode.MARKDOWN))

    """USER METHODS"""
    def send_user_template(self, update, context):

        product = products_table.find_one({"_id": self.order["product_id"]})

        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   product["image_id"],
    #                                order_template(order, product) + extra_str,
    #                                reply_markup=kb,
                                   parse_mode=ParseMode.MARKDOWN))

    def order_template(self, order, product):
        user_status = "⛔ ️🚫Продан" if order["status"] else "⚠ В ожидании ️"
        return product_template(product) + \
               strings["order_template"].format(
                   str(order['creation_timestamp']).split('.')[0],
                   user_status)


# class



    def product_template(self, product):
        """
        if product["_id"]:
            if orders_table.find_one({"product_id": product["_id"],
                                      "status": True}):
                product_status = "Продан⛔ ️"
            else:
                product_status = "В наличии ✅"

            return strings["product_template_2"].format(
                product["name"], product["price"], product["description"], product_status)
        return strings["product_template"].format(
            product["name"], product["price"], product["description"])
        """
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

def delete_messages(update, context):
    try:
        context.bot.delete_message(update.effective_chat.id, update.effective_message.message_id)
    except TelegramError:
        pass
    if 'to_delete' in context.user_data:
        for msg in context.user_data['to_delete']:
            try:
                if msg.message_id != update.effective_message.message_id:
                    context.bot.delete_message(update.effective_chat.id, msg.message_id)
            except TelegramError:
                # print('except in delete_message---> {}, {}'.format(e, msg.message_id))
                continue
        context.user_data['to_delete'] = list()
    else:
        context.user_data['to_delete'] = list()


def product_template(product):
    """
    if product["_id"]:
        if orders_table.find_one({"product_id": product["_id"],
                                  "status": True}):
            product_status = "Продан⛔ ️"
        else:
            product_status = "В наличии ✅"

        return strings["product_template_2"].format(
            product["name"], product["price"], product["description"], product_status)
    return strings["product_template"].format(
        product["name"], product["price"], product["description"])
    """
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


def send_product_template(update, context, product, extra_str="", kb=None, chat_id=None):
    context.user_data['to_delete'].append(
        context.bot.send_photo(chat_id if chat_id else update.effective_chat.id,
                               product["image_id"],
                               product_template(product) + extra_str,
                               reply_markup=kb,
                               parse_mode=ParseMode.MARKDOWN))


def order_template(order, product):
    user_status = "⛔ ️🚫Продан" if order["status"] else "⚠ В ожидании ️"
    return product_template(product) + \
           strings["order_template"].format(
               str(order['creation_timestamp']).split('.')[0],
               user_status)


def send_user_order_template(update, context, order_id, extra_str="", kb=None):
    if type(order_id) == str:
        order_id = ObjectId(order_id)
    order = orders_table.find_one({"_id": order_id})
    product = products_table.find_one({"_id": order["product_id"]})
    context.user_data["to_delete"].append(
        context.bot.send_photo(update.effective_chat.id,
                               product["image_id"],
                               order_template(order, product) + extra_str,
                               reply_markup=kb,
                               parse_mode=ParseMode.MARKDOWN))


def admin_order_template(order, product):
    # user_status = "🚫Удалён" if order["deleted_on_user_side"] else "⚠ В ожидании ️"
    # extra_string = "\n_Юзер отменил заказ. Можете смело удалять запись_" \
    #     if order["deleted_on_user_side"] else ""
    user_status = "⛔ ️🚫Продан" if order["status"] else "⚠ В ожидании ️"
    return product_template(product) + \
           strings["admin_order_template"].format(
               order["user_mention_markdown"],
               str(order['creation_timestamp']).split('.')[0],
               user_status)


def send_admin_order_template(update, context, order_id, extra_str="", kb=None):
    if type(order_id) == str:
        order_id = ObjectId(order_id)
    order = orders_table.find_one({"_id": order_id})
    # if not order:
    #     return False
    product = products_table.find_one({"_id": order["product_id"]})
    context.user_data["to_delete"].append(
        context.bot.send_photo(update.effective_chat.id,
                               product["image_id"],
                               admin_order_template(order, product) + extra_str,
                               reply_markup=kb,
                               parse_mode=ParseMode.MARKDOWN))


"""def send_short_order(update, context, order):
    # if type(order_id) == str:
    #     order_id = ObjectId(order_id)

    # order = orders_table.find_one({"_id": order_id})

    context.user_data["to_delete"].append(
        context.bot.send_message(update.effective_chat.id,
                                 strings["short_order_template"].format(
                                     order["user_mention_markdown"],
                                     str(order['creation_timestamp']).split('.')[0]),
                                 reply_markup=kb,
                                 parse_mode=ParseMode.MARKDOWN))"""


class Notification:
    @staticmethod
    def new_order(update, context, _id):
        extra_str = strings["new_order_notification"]
        product = products_table.find_one({"_id": _id})
        for chat_id in conf["ADMINS"]:
            send_product_template(update, context, product, extra_str, chat_id=chat_id)

    @staticmethod
    def new_product(update, context, _id):
        extra_str = f"\n\n{strings['success_adding']}"
        product = products_table.find_one({"_id": _id})
        for chat_id in conf["ADMINS"]:
            context.bot.send_photo(chat_id if chat_id else update.effective_chat.id,
                                   product["image_id"],
                                   product_template(product) + extra_str,
                                   parse_mode=ParseMode.MARKDOWN)

    @staticmethod
    def order_canceled(update, context):
        pass
