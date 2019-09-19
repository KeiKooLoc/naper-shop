from telegram.ext import CallbackContext, CommandHandler, \
    ConversationHandler, CallbackQueryHandler, MessageHandler, Filters, RegexHandler
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from db import orders_table, products_table
from helper import delete_messages, product_template, order_template, admin_order_template, send_product_template
import datetime
from config import conf
from math import ceil
import logging
from bson import ObjectId
from strings import strings


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


keyboards = dict(
    # USER SIDE
    start_kb=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["shop_btn"], callback_data="shop")],
         [InlineKeyboardButton(strings["my_orders"], callback_data="my_orders")],
         [InlineKeyboardButton(strings["contacts_btn"], callback_data="contacts")]]),

    back_to_user_main_menu_kb=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["back"], callback_data="back_to_user_main_menu")]]),

    confirm_order_kb=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["make_order_btn"], callback_data="confirm_order"),
          InlineKeyboardButton(strings["back"], callback_data="back_to_shop")]]),

    confirm_delete_order=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["delete_order_btn"], callback_data="finish_delete"),
          InlineKeyboardButton(strings["back"], callback_data="back_to_user_orders")]]),

    # ADMIN SIDE
    admin_start_kb=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["add_product_btn"], callback_data="add_product"),
          InlineKeyboardButton(strings["products_btn"], callback_data="all_products")],
         [InlineKeyboardButton(strings["orders_btn"], callback_data="all_orders")],
         [InlineKeyboardButton(strings["back"], callback_data="back_to_user_main_menu")]]),

    back_to_admin_main_menu_kb=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["back"], callback_data="back_to_admin_main_menu")]]),

    confirm_adding_product=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["add_btn"], callback_data="add"),
          InlineKeyboardButton(strings["back"], callback_data="back_to_admin_main_menu")]]),

    confirm_delete_product=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["delete_btn"], callback_data="delete_product"),
          InlineKeyboardButton(strings["back"], callback_data="back_to_all_products")]]),

    confirm_order_as_completed=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["back"], callback_data="back_to_all_orders"),
          InlineKeyboardButton(strings["mark_as_completed_btn"], callback_data="finish_mark_as_completed")]]),

    # confirm_order_status_to_sold=InlineKeyboardMarkup(
    #     [[InlineKeyboardButton(strings["change_to_sold"], callback_data="change_status"),
    #       InlineKeyboardButton(strings["back"], callback_data="back_to_admin_orders")]]),

    # confirm_order_status_to_not_sold=InlineKeyboardMarkup(
    #     [[InlineKeyboardButton(strings["change_to_not_sold"], callback_data="change_status"),
    #       InlineKeyboardButton(strings["back"], callback_data="back_to_admin_orders")]])
)


class Main(object):
    # Pagination keyboard logic
    def pagin(self, context, all_data, back_btn, per_page):
        total_pages = ceil(all_data.count() / per_page)
        # back_button = [InlineKeyboardButton(strings["back"], callback_data="back_to_user_main_menu")]
        # 0 - iter pages, 1 - filters buttons, 2 - back button
        pages_keyboard = [[], [], back_btn]
        # add filters buttons if it exist in user_data
        # if user_data.get("filters_buttons"):
        #     pages_keyboard[1].extend(user_data["filters_buttons"])
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
            # if orders_table.find_one({"user_id": update.effective_user.id,
            #                           "product_id": product["_id"],
            #                           # "status": True
            #                           }):
            #     kb = None
            # else:
            #     kb = InlineKeyboardMarkup(
            #         [[InlineKeyboardButton(strings["make_order_btn"],
            #                                callback_data=f"make_order/{product['_id']}")]])
            if product["sold"]:
                kb = None
            else:
                kb = InlineKeyboardMarkup([[InlineKeyboardButton(strings["make_order_btn"],
                                            callback_data=f"make_order/{product['_id']}")]])
            extra_string = ""
            if orders_table.find_one({"user_id": update.effective_user.id,
                                      "product_id": product["_id"],
                                     "deleted_on_user_side": False}):
                extra_string += "\n_У вас уже есть заказ с данным товаром_"

            # context.user_data['to_delete'].append(
            #     context.bot.send_photo(update.effective_chat.id,
            #                            product["image_id"],
            #                            product_template(product) +
            #                            extra_string,
            #                            reply_markup=kb,
            #                           parse_mode=ParseMode.MARKDOWN))
            send_product_template(update, context, product, extra_string, kb)
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
        # context.user_data['to_delete'].append(
        #     context.bot.send_photo(update.effective_chat.id,
        #                            context.user_data["order"]["image_id"],
        #                            product_template(context.user_data["order"]) +
        #                            strings["confirm_order"],
        #                            reply_markup=keyboards["confirm_order_kb"],
        #                            parse_mode=ParseMode.MARKDOWN))
        send_product_template(update, context, context.user_data["order"],
                              strings["confirm_order"], keyboards["confirm_order_kb"])
        return CONFIRM_ORDER

    def finish_making_order(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
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
            kb = InlineKeyboardMarkup(
                [[InlineKeyboardButton(strings["delete_order_btn"],
                                       callback_data=f"delete_order/{order['_id']}")]])
            product = products_table.find_one({"_id": order["product_id"]})
            context.user_data['to_delete'].append(
                context.bot.send_photo(update.effective_chat.id,
                                       product["image_id"],
                                       order_template(order, product),
                                       reply_markup=kb,
                                       parse_mode=ParseMode.MARKDOWN))
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
        product = products_table.find_one(
            {"_id": context.user_data["order"]["product_id"]})
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   context.user_data["order"]["product_object"]["image_id"],
                                   order_template(context.user_data["order"], product) +
                                   strings["delete_order"],
                                   reply_markup=keyboards["confirm_delete_order"],
                                   parse_mode=ParseMode.MARKDOWN))
        return CONFIRM_DELETE_ORDER

    def finish_delete_order(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        orders_table.update_one({"_id": ObjectId(update.callback_query.data.split('/')[1])},
                                {"$set": {"deleted_on_user_side": True}})
        update.callback_query.answer(text=strings["blink_success_delete_order"])
        return self.my_orders(update, context)

    def back_to_main_menu(self, update: Update, context: CallbackContext, msg_to_send=None):
        to_del = context.user_data.get('to_delete', list())
        context.user_data.clear()
        context.user_data['to_delete'] = to_del
        if msg_to_send:
            context.user_data["msg_to_send"] = msg_to_send
        return self.start(update, context)


class Admin(Main):
    def __init__(self):
        self.back_button = [InlineKeyboardButton(strings["back"], callback_data="back_to_admin_main_menu")]

    def start(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["to_delete"].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["admin_start_msg"],
                                     reply_markup=keyboards["admin_start_kb"]))
        return ConversationHandler.END

    def start_adding_product(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["to_delete"].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["add_image"],
                                     reply_markup=keyboards["back_to_admin_main_menu_kb"]))
        return SET_IMAGE

    def set_name(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        print(update.message.photo[-1].file_id)
        context.user_data["image_id"] = update.message.photo[-1].file_id
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   context.user_data["image_id"],
                                   strings["set_name"],
                                   reply_markup=keyboards["back_to_admin_main_menu_kb"]))
        return SET_NAME

    def set_price(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["name"] = update.message.text
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   context.user_data["image_id"],
                                   f"*Название:* `{context.user_data['name']}`"
                                   f"\n\n{strings['set_price']}",
                                   reply_markup=keyboards["back_to_admin_main_menu_kb"],
                                   parse_mode=ParseMode.MARKDOWN))
        return SET_PRICE

    def set_description(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["price"] = update.message.text
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   context.user_data["image_id"],
                                   f"*Название:* `{context.user_data['name']}`"
                                   f"\n*Цена:* `{context.user_data['price']}`"
                                   f"\n\n{strings['set_description']}",
                                   reply_markup=keyboards["back_to_admin_main_menu_kb"],
                                   parse_mode=ParseMode.MARKDOWN))
        return SET_DESCRIPTION

    def confirm_adding(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["description"] = update.message.text
        # context.user_data["to_delete"].append(
        #     context.bot.send_photo(update.effective_chat.id,
        #                            context.user_data["image_id"],
        #                            product_template(context.user_data) +
        #                            f"\n\n{strings['confirm_adding']}",
        #                            reply_markup=keyboards["confirm_adding_product"],
        #                            parse_mode=ParseMode.MARKDOWN))
        send_product_template(update, context, context.user_data,
                              f"\n\n{strings['confirm_adding']}",
                              keyboards["confirm_adding_product"])

        return CONFIRM_ADDING

    def finish_adding(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        products_table.insert_one({"name": context.user_data["name"],
                                   "price": context.user_data["price"],
                                   "description": context.user_data["description"],
                                   "image_id": context.user_data["image_id"],
                                   "timestamp": datetime.datetime.now(),
                                   "sold": False})
        context.bot.send_photo(update.effective_chat.id,
                               context.user_data["image_id"],
                               f"{strings['success_adding']}" +
                               product_template(context.user_data),
                               parse_mode=ParseMode.MARKDOWN)
        msg = strings["success_adding"]
        return self.back_to_main_menu(update, context, msg)

    def all_orders(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        try:
            context.user_data['page'] = int(update.callback_query.data)
        except ValueError:
            if update.callback_query.data == 'all_orders':
                context.user_data['page'] = 1
        self.send_orders_layout(update, context)
        return ADMIN_ORDERS_INBOX

    def send_orders_layout(self, update, context):
        per_page = conf["ORDERS_PER_PAGE"]
        # Take users reports from db
        all_data = orders_table.find().sort([["_id", -1]])
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
            # orders_table.find({})
            kb = [[InlineKeyboardButton(strings["mark_as_completed_btn"],
                                        callback_data=f"mark_as_completed/{order['_id']}")]]
            if order["deleted_on_user_side"]:
                kb = [[InlineKeyboardButton(strings["delete_order_btn"],
                                            callback_data=f"delete_order/{order['_id']}")]]

            product = products_table.find_one({"_id": order["product_id"]})
            context.user_data['to_delete'].append(
                context.bot.send_photo(update.effective_chat.id,
                                       product["image_id"],
                                       admin_order_template(order, product),
                                       reply_markup=InlineKeyboardMarkup(kb),
                                       parse_mode=ParseMode.MARKDOWN))
        # Pages navigation
        context.user_data['to_delete'].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["current_page"].format(context.user_data['page']),
                                     reply_markup=self.pagin(context, all_data, self.back_button, per_page),
                                     parse_mode=ParseMode.MARKDOWN))

    def delete_order(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        orders_table.delete_one({"_id": ObjectId(update.callback_query.data.split('/')[1])})
        update.callback_query.answer(text=strings["blink_success_delete_order"])
        return self.all_orders(update, context)

    """
    def confirm_change_status(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["order"] = orders_table.find_one(
            {"_id": ObjectId(update.callback_query.data.split('/')[1])})
        context.user_data["product"] = products_table.find_one(
            {"_id": context.user_data["order"]["product_id"]})
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   context.user_data["product"]["image_id"],
                                   strings["confirm_order_status_to_not_sold"
                                           if context.user_data["product"]["status"] else
                                           "confirm_order_status_to_sold"] +
                                   admin_order_template(context.user_data["order"],
                                                        context.user_data["product"]),
                                   reply_markup=keyboards["confirm_change_order_status"],
                                   parse_mode=ParseMode.MARKDOWN))
        return CONFIRM_CHANGE_ORDER_STATUS
    
    """
    """ 
    def finish_change_status(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        orders_table.update_one({"_id": context.user_data["order"]["_id"]},
                                {"status": False if context.user_data["order"]["status"] else True})
        return self.back_to_main_menu(update, context, self.start)
    """

    def confirm_mark_as_completed(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["order"] = orders_table.find_one(
            {"_id": ObjectId(update.callback_query.data.split('/')[1])})
        context.user_data["product"] = products_table.find_one(
            {"_id": context.user_data["order"]["product_id"]})
        context.user_data["to_delete"].append(
            context.bot.send_photo(update.effective_chat.id,
                                   context.user_data["product"]["image_id"],
                                   admin_order_template(context.user_data["order"],
                                                        context.user_data["product"]) +
                                   strings["mark_as_completed"],
                                   reply_markup=keyboards["confirm_change_order_status"],
                                   parse_mode=ParseMode.MARKDOWN))
        return CONFIRM_MARK_COMPLETED

    def finish_mark_as_completed(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        orders_table.update_one({"_id": context.user_data["order"]["_id"]},
                                {"$set": {"status": True}})
        products_table.update_one({"_id": context.user_data["order"]["product_id"]},
                                  {"$set": {"sold": True}})
        update.callback_query.answer(text=strings["blink_success_marked_as_completed"])
        return self.all_orders(update, context)

    def all_products(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        try:
            context.user_data['page'] = int(update.callback_query.data)
        except ValueError:
            if update.callback_query.data == 'all_products':
                context.user_data['page'] = 1
        self.send_products_layout(update, context)
        return ALL_PRODUCTS

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
            if not product["sold"]:
                kb = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(strings["delete_product"],
                                           callback_data=f"delete_product/{product['_id']}"),
                      InlineKeyboardButton(strings["mark_as_sold_btn"],
                                           callback_data=f"change_product_status/{product['_id']}")]])
            else:
                kb = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(strings["delete_product"],
                                           callback_data=f"delete_product/{product['_id']}"),
                      InlineKeyboardButton(strings["mark_as_in_stock_btn"],
                                           callback_data=f"change_product_status/{product['_id']}")]])
            # context.user_data['to_delete'].append(
            #     context.bot.send_photo(update.effective_chat.id,
            #                            product["image_id"],
            #                            product_template(product),
            #                            reply_markup=kb,
            #                            parse_mode=ParseMode.MARKDOWN))
            send_product_template(update, context, product, kb=kb)
        # Pages navigation
        context.user_data['to_delete'].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["current_page"].format(context.user_data['page']),
                                     reply_markup=self.pagin(context, all_data, self.back_button, per_page),
                                     parse_mode=ParseMode.MARKDOWN))

    def confirm_delete_product(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["product"] = products_table.find_one(
            {"_id": ObjectId(update.callback_query.data.split('/')[1])})
        # context.user_data["to_delete"].append(
        #     context.bot.send_photo(update.effective_chat.id,
        #                            context.user_data["product"]["image_id"],
        #                            product_template(context.user_data["product"]) +
        #                            strings["confirm_delete"],
        #                            reply_markup=keyboards["confirm_delete_product"],
        #                           parse_mode=ParseMode.MARKDOWN))
        send_product_template(update, context,
                              context.user_data["product"],
                              strings["confirm_delete"],
                              keyboards["confirm_delete_product"])

        return CONFIRM_DELETE_PRODUCT

    def finish_delete_product(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        products_table.delete_one({"_id": context.user_data["product"]["_id"]})
        # orders_table.delete_many({"product_id": context.user_data["product"]["_id"]})
        update.callback_query.answer(text=strings["blink_success_deleted_product"])
        return self.all_products(update, context)

    def confirm_change_product_status(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["product"] = products_table.find_one(
            {"_id": ObjectId(update.callback_query.data.split('/')[1])})
        if context.user_data["product"]["sold"]:
            string = strings["confirm_product_status_to_in_stock"]
            kb = [[InlineKeyboardButton(strings["back"],
                                        callback_data="back_to_all_products"),
                   InlineKeyboardButton(strings["mark_as_in_stock_btn"],
                                        callback_data="confirm_change_product_status")]]
        else:
            string = strings["confirm_product_status_to_sold"]
            kb = [[InlineKeyboardButton(strings["back"],
                                        callback_data="back_to_all_products"),
                   InlineKeyboardButton(strings["mark_as_sold_btn"],
                                        callback_data="confirm_change_product_status")]]

        # context.user_data["to_delete"].append(
        #     context.bot.send_photo(update.effective_chat.id,
        #                            context.user_data["product"]["image_id"],
        #                            product_template(context.user_data["product"]) +
        #                            string,
        #                            reply_markup=InlineKeyboardMarkup(kb),
        #                            parse_mode=ParseMode.MARKDOWN))
        send_product_template(update, context,
                              context.user_data["product"],
                              string, InlineKeyboardMarkup(kb))
        return CONFIRM_CHANGE_PRODUCT_STATUS

    def finish_change_product_status(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        products_table.update_one({"_id": context.user_data["product"]["_id"]},
                                  {"$set": {"sold": False if context.user_data["product"]["sold"] else True}})
        update.callback_query.answer(text=strings["blink_success_changed_product_status"])
        return self.all_products(update, context)

    def back_to_main_menu(self, update, context, msg_to_send=None):
        to_del = context.user_data.get('to_delete', list())
        context.user_data.clear()
        context.user_data['to_delete'] = to_del
        if msg_to_send:
            context.user_data["msg_to_send"] = msg_to_send
        return self.start(update, context)


# USER SIDE
SHOP, CONFIRM_ORDER, USER_ORDERS_INBOX, CONFIRM_DELETE_ORDER = range(4)

START_HANDLER = CommandHandler("start", User().start)

CONTACTS_HANDLER = CallbackQueryHandler(User().contacts, pattern=r"contacts")

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


# ADMIN SIDE
SET_IMAGE, SET_NAME, SET_PRICE, SET_DESCRIPTION, \
    CONFIRM_ADDING, ADMIN_ORDERS_INBOX, CONFIRM_CHANGE_ORDER_STATUS,\
    ALL_PRODUCTS, CONFIRM_DELETE_PRODUCT, CONFIRM_CHANGE_PRODUCT_STATUS,\
    CONFIRM_MARK_COMPLETED = range(11)

ADMIN_START_HANDLER = CommandHandler("a", Admin().start)

BACK_TO_USER_MENU = CallbackQueryHandler(User().back_to_main_menu, pattern=r"back_to_user_main_menu")

ADMIN_ORDERS_HANDLER = ConversationHandler(
    entry_points=[CallbackQueryHandler(Admin().all_orders, pattern=r"all_orders")],
    states={
        ADMIN_ORDERS_INBOX: [CallbackQueryHandler(Admin().all_orders, pattern="^[0-9]+$"),
                             CallbackQueryHandler(Admin().confirm_mark_as_completed,
                                                  pattern=r"mark_as_completed"),
                             CallbackQueryHandler(Admin().delete_order, pattern=r"delete_order")],

        CONFIRM_MARK_COMPLETED: [CallbackQueryHandler(Admin().finish_mark_as_completed,
                                                      pattern=r"finish_mark_as_completed"),
                                 CallbackQueryHandler(Admin().all_orders,
                                                      pattern=r"back_to_all_orders")]
    },
    fallbacks=[CallbackQueryHandler(Admin().back_to_main_menu, pattern=r"back_to_admin_main_menu")]
)

ADD_PRODUCT_HANDLER = ConversationHandler(
    entry_points=[CallbackQueryHandler(Admin().start_adding_product, pattern=r"add_product")],
    states={
        SET_IMAGE: [MessageHandler(Filters.photo, Admin().set_name)],

        SET_NAME: [MessageHandler(Filters.text, Admin().set_price)],

        SET_PRICE: [  # MessageHandler(Filters.text, Admin().set_description)
                    # RegexHandler("^[0-9]+$", Admin().set_description)
                    MessageHandler(Filters.regex("^[0-9]+$"), Admin().set_description)],

        SET_DESCRIPTION: [MessageHandler(Filters.text, Admin().confirm_adding)],

        CONFIRM_ADDING: [CallbackQueryHandler(Admin().finish_adding, pattern=r"add")]
    },
    fallbacks=[CallbackQueryHandler(Admin().back_to_main_menu, pattern=r"back_to_admin_main_menu")]
)

ADMIN_PRODUCTS_HANDLER = ConversationHandler(
    entry_points=[CallbackQueryHandler(Admin().all_products, pattern=r"all_products")],
    states={
        ALL_PRODUCTS: [CallbackQueryHandler(Admin().all_products, pattern="^[0-9]+$"),
                       CallbackQueryHandler(Admin().confirm_delete_product, pattern=r"delete_product"),
                       CallbackQueryHandler(Admin().confirm_change_product_status, pattern=r"change_product_status")],

        CONFIRM_DELETE_PRODUCT: [CallbackQueryHandler(Admin().finish_delete_product, pattern=r"delete_product"),
                                 CallbackQueryHandler(Admin().all_products, pattern=r"back_to_all_products")],

        CONFIRM_CHANGE_PRODUCT_STATUS: [CallbackQueryHandler(Admin().finish_change_product_status,
                                                             pattern=r"confirm_change_product_status"),
                                        CallbackQueryHandler(Admin().all_products,
                                                             pattern=r"back_to_all_products")],
    },
    fallbacks=[CallbackQueryHandler(Admin().back_to_main_menu, pattern=r"back_to_admin_main_menu")]
)
