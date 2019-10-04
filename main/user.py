from telegram.ext import CallbackContext, CommandHandler, \
    ConversationHandler, CallbackQueryHandler, MessageHandler, Filters, RegexHandler
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from db import orders_table, products_table
from .helper.helper import delete_messages
from .helper.templates_models import Order, Product
import datetime
from config import conf
from math import ceil
import logging
from bson import ObjectId
from .helper.strings import strings
import time


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


keyboards = dict(
    # USER SIDE
    start_kb=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["shop_btn"], callback_data="shop")],
         [InlineKeyboardButton(strings["my_orders"], callback_data="my_orders")],
         [InlineKeyboardButton(strings["contacts_btn"], callback_data="contacts"),
          InlineKeyboardButton(strings["terms_btn"], callback_data="terms")]]),

    back_to_user_main_menu_kb=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["back"], callback_data="back_to_user_main_menu")]]),

    confirm_order_kb=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["make_order_btn"], callback_data="confirm_order"),
          InlineKeyboardButton(strings["back"], callback_data="back_to_shop")]]),

    confirm_delete_order=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["delete_order_btn"], callback_data="finish_delete"),
          InlineKeyboardButton(strings["back"], callback_data="back_to_user_orders")]]))


class Main(object):
    # Pagination keyboard logic
    def pagin(self, context, all_data, back_btn, per_page):
        total_pages = ceil(all_data.count() / per_page)
        # add filters buttons if it exist in user_data
        if context.user_data.get("extra_pagin_btn"):
            pages_keyboard = [[]]
            pages_keyboard.extend(context.user_data["extra_pagin_btn"])
            pages_keyboard.append(back_btn)
        else:
            pages_keyboard = [[], back_btn]
        # if only one page don't show pagination
        if total_pages <= 1:
            pass
        # if total pages count <= 8 - show all 8 buttons in pagination
        elif 2 <= total_pages <= 8:
            for i in range(1, total_pages + 1):
                pages_keyboard[0].append(
                    InlineKeyboardButton('|' + str(i) + '|', callback_data=i)
                    if i == context.user_data['page'] else
                    InlineKeyboardButton(str(i), callback_data=i))
        # if total pages count > 8 - create pagination
        else:
            arr = [i if i in range(context.user_data['page'] - 1, context.user_data['page'] + 3) else
                   i if i == total_pages else
                   i if i == 1 else
                   # str_to_remove
                   '' for i in range(1, total_pages + 1)]
            p_index = arr.index(context.user_data['page'])
            layout = list(dict.fromkeys(arr[:p_index])) + \
                     list(dict.fromkeys(arr[p_index:]))
            for num, i in enumerate(layout):
                if i == '':
                    pages_keyboard[0].append(InlineKeyboardButton('...',
                                                                  callback_data=layout[num - 1] + 1
                                                                  if num > layout.index(context.user_data['page']) else
                                                                  layout[num + 1] - 1))
                else:
                    pages_keyboard[0].append(InlineKeyboardButton('|' + str(i) + '|', callback_data=i)
                                             if i == context.user_data['page'] else
                                             InlineKeyboardButton(str(i), callback_data=i))
        return InlineKeyboardMarkup(pages_keyboard)

    """
    def back_to_main_menu(self, update, context, start_func=None, msg_to_send=None):
        to_del = context.user_data.get('to_delete', list())
        context.user_data.clear()
        context.user_data['to_delete'] = to_del
        if msg_to_send:
            context.user_data["msg_to_send"] = msg_to_send
        if start_func:
            return start_func(update, context)
        else:
            return User().start(update, context)
    """


class User(Main):
    def __init__(self):
        self.back_button = [InlineKeyboardButton(strings["back"], callback_data="back_to_user_main_menu")]

    def start(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        if context.user_data.get("msg_to_send"):
            context.user_data["to_delete"].append(
                context.bot.send_message(update.effective_chat.id,
                                         context.user_data["msg_to_send"]))
        context.user_data["to_delete"].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["start_msg"],
                                     reply_markup=keyboards["start_kb"]))
        return ConversationHandler.END

    def contacts(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["to_delete"].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["contacts"],
                                     reply_markup=keyboards["back_to_user_main_menu_kb"],
                                     parse_mode=ParseMode.MARKDOWN))
        return ConversationHandler.END

    def terms(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["to_delete"].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["terms_msg"],
                                     reply_markup=keyboards["back_to_user_main_menu_kb"],
                                     parse_mode=ParseMode.MARKDOWN))
        return ConversationHandler.END

    def shop(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        try:
            context.user_data['page'] = int(update.callback_query.data)
        except ValueError:
            if update.callback_query.data == 'shop':
                context.user_data['page'] = 1
        self.send_products_layout(update, context)
        return SHOP

    def send_products_layout(self, update, context):
        per_page = conf["PRODUCTS_PER_PAGE"]
        # Take users reports from db
        all_data = products_table.find().sort([["_id", -1]])
        # if no documents - send notification message
        if all_data.count() == 0:
            context.user_data["to_delete"].append(
                context.bot.send_message(update.effective_chat.id,
                                         strings["no_products"]))
        # if page is first - take first n items
        if context.user_data["page"] == 1:
            data_to_send = all_data.limit(per_page)
        # if page is not first - take items on given page
        else:
            last_on_prev_page = (context.user_data["page"] - 1) * per_page
            data_to_send = [i for i in all_data[last_on_prev_page:last_on_prev_page + per_page]]

        # SENDING DATA
        # Title
        context.user_data['to_delete'].append(
            context.bot.send_message(update.callback_query.message.chat_id,
                                     strings["shop_title"].format(all_data.count()),
                                     parse_mode=ParseMode.MARKDOWN))
        # Products
        for product in data_to_send:
            # todo: fix this coz of repeating in template
            extra_str = ""
            kb = None
            if not product["sold"]:
                kb = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(strings["make_order_btn"],
                                           callback_data=f"make_order/{product['_id']}")]])
            if orders_table.find_one(
                    {"user_id": update.effective_user.id,
                     "product_id": product["_id"],
                     "deleted_on_user_side": False}):
                extra_str += "\n\n_У вас уже есть заказ с данным товаром_"
                kb = None
            Product(product_dict=product).send_product_template(update, context, extra_str, kb)
            # send_product_template(update, context, product, extra_string, kb)
        # Pages navigation
        context.user_data['to_delete'].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["current_page"].format(context.user_data['page']),
                                     reply_markup=self.pagin(context, all_data, self.back_button, per_page),
                                     parse_mode=ParseMode.MARKDOWN))

    def make_order(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["order"] = products_table.find_one(
            {'_id': ObjectId(update.callback_query.data.split('/')[1])})
        Product(product_dict=context.user_data["order"]).send_product_template(
            update, context, strings["confirm_order"], keyboards["confirm_order_kb"])
        # send_product_template(update, context, context.user_data["order"],
        #                       strings["confirm_order"], keyboards["confirm_order_kb"])
        return CONFIRM_ORDER

    def finish_making_order(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        """
        already_exist_order = orders_table.find_one({"user_id": update.effective_user.id,
                                                     "product_id": context.user_data["order"]["_id"]})
        if already_exist_order:
            orders_table.update_one({"user_id": update.effective_user.id,
                                     "product_id": context.user_data["order"]["_id"],
                                     "creation_timestamp": datetime.datetime.now(),
                                     "deleted_on_user_side": False,
                                     "status": False,
                                     })
        else:
            orders_table.insert_one({"user_id": update.effective_user.id,
                                     "chat_id": update.effective_chat.id,
                                     "user_mention_markdown": update.effective_user.mention_markdown(),
                                     "product_id": context.user_data["order"]["_id"],
                                     "product_object": context.user_data["order"],
                                     "creation_timestamp": datetime.datetime.now(),
                                     "status": False,
                                     "sold_timestamp": None,
                                     "deleted_on_user_side": False})

        """
        _id = orders_table.insert_one(
            {"user_id": update.effective_user.id,
             "chat_id": update.effective_chat.id,
             "user_mention_markdown": update.effective_user.mention_markdown(),
             "product_id": context.user_data["order"]["_id"],
             "product_object": context.user_data["order"],
             "creation_timestamp": datetime.datetime.now(),
             "status": False,
             "sold_timestamp": None,
             "deleted_on_user_side": False}).inserted_id
        # Notification.new_order(update, context, _id)
        # time.sleep(0.5)
        Order(_id=_id).new_order_notification(context)

        msg = strings["order_created"]
        return self.back_to_main_menu(update, context, msg)

    def my_orders(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        try:
            context.user_data['page'] = int(update.callback_query.data)
        except ValueError:
            if update.callback_query.data == 'my_orders':
                context.user_data['page'] = 1
        self.send_orders_layout(update, context)
        return USER_ORDERS_INBOX

    def send_orders_layout(self, update, context):
        per_page = conf["ORDERS_PER_PAGE"]
        # Take users reports from db
        all_data = orders_table.find({"user_id": update.effective_user.id,
                                      "deleted_on_user_side": False}).sort([["_id", -1]])
        # if no documents - send notification message
        if all_data.count() == 0:
            context.user_data["to_delete"].append(
                context.bot.send_message(update.effective_chat.id,
                                         strings["no_orders"]))
        # if page is first - take first n items
        if context.user_data["page"] == 1:
            data_to_send = all_data.limit(per_page)
        # if page is not first - take items on given page
        else:
            last_on_prev_page = (context.user_data["page"] - 1) * per_page
            data_to_send = [i for i in all_data[last_on_prev_page:last_on_prev_page + per_page]]

        # SENDING DATA
        # Title
        context.user_data['to_delete'].append(
            context.bot.send_message(update.callback_query.message.chat_id,
                                     strings["orders_title"].format(all_data.count()),
                                     parse_mode=ParseMode.MARKDOWN))
        # Orders
        for order in data_to_send:
            kb = None if order["status"] else InlineKeyboardMarkup(
                [[InlineKeyboardButton(strings["delete_order_btn"],
                                       callback_data=f"delete_order/{order['_id']}")]])
            Order(order_dict=order).send_user_template(update, context, kb=kb)

            # if not order["status"]:
            #     kb = InlineKeyboardMarkup(
            #         [[InlineKeyboardButton(strings["delete_order_btn"],
            #                                callback_data=f"delete_order/{order['_id']}")]])

            # product = products_table.find_one({"_id": order["product_id"]})
            # context.user_data['to_delete'].append(
            #     context.bot.send_photo(update.effective_chat.id,
            #                            product["image_id"],
            #                           order_template(order, product),
            #                            reply_markup=kb,
            #                            parse_mode=ParseMode.MARKDOWN))
        # Pages navigation
        context.user_data['to_delete'].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["current_page"].format(context.user_data['page']),
                                     reply_markup=self.pagin(context, all_data, self.back_button, per_page),
                                     parse_mode=ParseMode.MARKDOWN))

    def confirm_delete_order(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["order"] = orders_table.find_one(
            {"_id": ObjectId(update.callback_query.data.split('/')[1])})
        # product = products_table.find_one(
        #     {"_id": context.user_data["order"]["product_id"]})
        # todo
        # if context.user_data["order"] and product:
        #     pass
        # else:
        #     "ваш заказ уже удалён потому что товар был продан или удалён"

        # context.user_data["to_delete"].append(
        #     context.bot.send_photo(update.effective_chat.id,
        #                            context.user_data["order"]["product_object"]["image_id"],
        #                            order_template(context.user_data["order"], product) +
        #                            strings["delete_order"],
        #                            reply_markup=keyboards["confirm_delete_order"],
        #                            parse_mode=ParseMode.MARKDOWN))
        Order(order_dict=context.user_data["order"]).send_user_template(
            update, context, strings["delete_order"], keyboards["confirm_delete_order"])
        return CONFIRM_DELETE_ORDER

    def finish_delete_order(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        # orders_table.update_one({"_id": ObjectId(update.callback_query.data.split('/')[1])},
        #                         {"$set": {"deleted_on_user_side": True}})
        orders_table.delete_one({"_id": context.user_data["order"]["_id"]})
        update.callback_query.answer(text=strings["blink_success_delete_order"])
        return self.my_orders(update, context)

    def back_to_main_menu(self, update: Update, context: CallbackContext, msg_to_send=None):
        to_del = context.user_data.get('to_delete', list())
        context.user_data.clear()
        context.user_data['to_delete'] = to_del
        if msg_to_send:
            context.user_data["msg_to_send"] = msg_to_send
        return self.start(update, context)


# USER SIDE
SHOP, CONFIRM_ORDER, USER_ORDERS_INBOX, CONFIRM_DELETE_ORDER = range(4)

START_HANDLER = CommandHandler("start", User().start)

BACK_TO_USER_MENU = CallbackQueryHandler(User().back_to_main_menu, pattern=r"back_to_user_main_menu")

CONTACTS_HANDLER = CallbackQueryHandler(User().contacts, pattern=r"contacts")

TERMS_HANDLER = CallbackQueryHandler(User().terms, pattern=r"terms")

SHOP_HANDLER = ConversationHandler(
    entry_points=[CallbackQueryHandler(User().shop, pattern=r"shop")],
    states={
        SHOP: [CallbackQueryHandler(User().shop, pattern="^[0-9]+$"),
               CallbackQueryHandler(User().make_order, pattern=r"make_order")],
        CONFIRM_ORDER: [CallbackQueryHandler(User().finish_making_order, pattern=r"confirm_order"),
                        CallbackQueryHandler(User().shop, pattern=r"back_to_shop")]
    },
    fallbacks=[CallbackQueryHandler(User().back_to_main_menu, pattern=r"back_to_user_main_menu")]
)

USER_ORDERS_HANDLER = ConversationHandler(
    entry_points=[CallbackQueryHandler(User().my_orders, pattern=r"my_orders")],
    states={
        USER_ORDERS_INBOX: [CallbackQueryHandler(User().my_orders, pattern="^[0-9]+$"),
                            CallbackQueryHandler(User().confirm_delete_order, pattern=r"delete_order")],
        CONFIRM_DELETE_ORDER: [
            CallbackQueryHandler(User().finish_delete_order, pattern=r"finish_delete"),
            CallbackQueryHandler(User().my_orders, pattern=r"back_to_user_orders")
        ]

    },
    fallbacks=[CallbackQueryHandler(User().back_to_main_menu, pattern=r"back_to_user_main_menu")])
