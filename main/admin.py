import logging
import datetime
from bson import ObjectId
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          CallbackQueryHandler, MessageHandler, Filters)
from .user import Main
from config import conf
from .helper.strings import strings
from .helper.helper import delete_messages
from db import orders_table, products_table
from .helper.templates_models import Order, Product

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

keyboards = dict(
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

    confirm_sell_product=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["mark_as_completed_btn"], callback_data="finish_sell"),
          InlineKeyboardButton(strings["back"], callback_data="back_to_all_products")]]),

    back_to_all_products=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["back"], callback_data="back_to_all_products")]]),

    confirm_mark_as_in_stock=InlineKeyboardMarkup(
        [[InlineKeyboardButton(strings["mark_as_in_stock_btn"], callback_data="mark_as_in_stock"),
          InlineKeyboardButton(strings["back"], callback_data="back_to_all_products")]])

    # confirm_order_as_completed=InlineKeyboardMarkup(
    #     [[InlineKeyboardButton(strings["back"], callback_data="back_to_all_orders"),
    #       InlineKeyboardButton(strings["mark_as_completed_btn"], callback_data="finish_mark_as_completed")]]),

    # confirm_order_status_to_sold=InlineKeyboardMarkup(
    #     [[InlineKeyboardButton(strings["change_to_sold"], callback_data="change_status"),
    #       InlineKeyboardButton(strings["back"], callback_data="back_to_admin_orders")]]),

    # confirm_order_status_to_not_sold=InlineKeyboardMarkup(
    #     [[InlineKeyboardButton(strings["change_to_not_sold"], callback_data="change_status"),
    #       InlineKeyboardButton(strings["back"], callback_data="back_to_admin_orders")]])
)


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
        Product(product_dict=context.user_data).send_product_template(
            update, context, f"\n\n{strings['confirm_adding']}",
            keyboards["confirm_adding_product"])

        return CONFIRM_ADDING

    def finish_adding(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        _id = products_table.insert_one(
            {"name": context.user_data["name"],
             "price": context.user_data["price"],
             "description": context.user_data["description"],
             "image_id": context.user_data["image_id"],
             "timestamp": datetime.datetime.now(),
             "sold": False,
             "deleted": False}).inserted_id
        Product(_id=_id).new_product_notification(context)
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

    def send_orders_layout(self, update, context, choose_kb=False):
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
        title = f"{strings['select_buyer_title']}" \
                f"\n{Product(product_dict=context.user_data['product']).template()}" \
            if choose_kb else strings["orders_title"].format(all_data.count())
        context.user_data['to_delete'].append(
            context.bot.send_message(update.callback_query.message.chat_id,
                                     title,
                                     parse_mode=ParseMode.MARKDOWN))
        # Orders
        for order in data_to_send:
            if choose_kb:
                Order(order_dict=order).send_short_template(update, context)
            else:
                Order(order_dict=order).send_admin_template(update, context)
        # Pages navigation
        context.user_data['to_delete'].append(
            context.bot.send_message(update.effective_chat.id,
                                     strings["current_page"].format(context.user_data['page']),
                                     reply_markup=self.pagin(context, all_data, self.back_button, per_page),
                                     parse_mode=ParseMode.MARKDOWN))

    """ 
    def delete_order(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        orders_table.delete_one({"_id": ObjectId(update.callback_query.data.split('/')[1])})
        update.callback_query.answer(text=strings["blink_success_delete_order"])
        return self.all_orders(update, context)
    
    
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


 
    def finish_change_status(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        orders_table.update_one({"_id": context.user_data["order"]["_id"]},
                                {"status": False if context.user_data["order"]["status"] else True})
        return self.back_to_main_menu(update, context, self.start)


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
    """

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
            kb = [[InlineKeyboardButton(
                strings["delete_product"],
                callback_data=f"delete_product/{product['_id']}")], []]

            if product["sold"]:
                kb[1].append(InlineKeyboardButton(
                    strings["mark_as_in_stock_btn"],
                    callback_data=f"mark_as_in_stock/{product['_id']}"))
            else:
                kb[1].append(InlineKeyboardButton(
                    strings["mark_as_sold_btn"],
                    callback_data=f"mark_as_sold/{product['_id']}"))

            Product(product_dict=product).send_product_template(
                update, context, kb=InlineKeyboardMarkup(kb))
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
        Product(product_dict=context.user_data["product"]).send_product_template(
            update, context, strings["confirm_delete"], keyboards["confirm_delete_product"])
        return CONFIRM_DELETE_PRODUCT

    def finish_delete_product(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        products_table.delete_one({"_id": context.user_data["product"]["_id"]})
        # orders_table.find({""})
        orders_table.delete_many({"product_id": context.user_data["product"]["_id"],
                                  "status": False})
        update.callback_query.answer(text=strings["blink_success_deleted_product"])
        self.all_products(update, context)
        return ALL_PRODUCTS

    def choose_buyer(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        if update.callback_query.data.startswith("mark_as_sold"):
            context.user_data["product"] = products_table.find_one(
                {"_id": ObjectId(update.callback_query.data.split('/')[1])})
        try:
            context.user_data['page'] = int(update.callback_query.data)
        except ValueError:
            if update.callback_query.data == 'all_orders':
                context.user_data['page'] = 1
        context.user_data["extra_pagin_btn"] = [[InlineKeyboardButton(
            strings["not_telegram_client_btn"], callback_data="set_not_telegram_buyer")]]
        self.send_orders_layout(update, context, choose_kb=True)
        return CHOOSE_BUYER

    # def set_not_telegram_buyer(self, update: Update, context: CallbackContext):
    #     delete_messages(update, context)
    #     send_product_template(update, context,
    #                           context.user_data["product"],
    #                           strings["set_not_tel_buyer"],
    #                           kb=keyboards["back_to_all_products"])
    #     return SET_NOT_TELEGRAM_BUYER

    # def confirm_sell_not_tel_buyer(self, update: Update, context: CallbackContext):
    #     delete_messages(update, context)

    def confirm_sell(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["order_id"] = update.callback_query.data.split('/')[1]
        Order(_id=context.user_data["order_id"]).send_admin_template(
            update, context, strings["confirm_sell_product"],
            keyboards["confirm_sell_product"])
        return CONFIRM_SELL

    def finish_sell_not_tel(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        products_table.update_one({"_id": context.user_data["product"]["_id"]},
                                  {"$set": {"sold": True}})
        orders_table.delete_many({"product_id": context.user_data["product"]["_id"],
                                  "status": False})
        update.callback_query.answer(text=strings["blink_product_sold"])
        self.back_to_main_menu(update, context)

    def finish_sell(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["product"]["sold"] = True
        orders_table.update_one({"_id": ObjectId(context.user_data["order_id"])},
                                {"$set": {"status": True,
                                          "product_object": context.user_data["product"]}})
        products_table.update_one({"_id": context.user_data["product"]["_id"]},
                                  {"$set": {"sold": True}})
        orders_table.delete_many({"product_id": context.user_data["product"]["_id"],
                                  "_id": {"$ne": ObjectId(context.user_data["order_id"])}})
        update.callback_query.answer(text=strings["blink_product_sold"])
        return self.back_to_main_menu(update, context)

    def confirm_mark_as_in_stock(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["product_id"] = update.callback_query.data.split('/')[1]
        Product(_id=context.user_data["product_id"]).send_product_template(
            update, context, strings["confirm_mark_as_in_stock"],
            keyboards["confirm_mark_as_in_stock"])
        return CONFIRM_MARK_IN_STOCK

    def put_in_stock(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        products_table.update_one({"_id": ObjectId(context.user_data["product_id"])},
                                  {"$set": {"sold": False}})
        update.callback_query.answer(text=strings["blink_product_in_stock"])
        return self.back_to_main_menu(update, context)

    """ 
    def confirm_change_product_status(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        context.user_data["product"] = products_table.find_one(
            {"_id": ObjectId(update.callback_query.data.split('/')[1])})
        kb = [[InlineKeyboardButton(strings["back"],
                                    callback_data="back_to_all_products")]]
        if context.user_data["product"]["sold"]:
            string = strings["confirm_product_status_to_in_stock"]
            kb[0].append(InlineKeyboardButton(strings["mark_as_in_stock_btn"],
                                              callback_data="confirm_change_product_status"))
        else:
            string = strings["confirm_product_status_to_sold"]
            kb[0].append(InlineKeyboardButton(strings["mark_as_sold_btn"],
                                              callback_data="confirm_change_product_status"))

        send_product_template(update, context,
                              context.user_data["product"],
                              string, InlineKeyboardMarkup(kb))
        return CONFIRM_CHANGE_PRODUCT_STATUS

    def finish_change_product_status(self, update: Update, context: CallbackContext):
        delete_messages(update, context)
        if context.user_data["product"]["sold"]:
            products_table.update_one({"_id": context.user_data["product"]["_id"]},
                                      {"$set": {"sold": False}})
            update.callback_query.answer(text=strings["blink_product_in_stock"])

        else:
            pass

        products_table.update_one({"_id": context.user_data["product"]["_id"]},
                                  {"$set": {"sold": False if context.user_data["product"]["sold"] else True}})
        return self.all_products(update, context)
    """

    def back_to_main_menu(self, update, context, msg_to_send=None):
        to_del = context.user_data.get('to_delete', list())
        context.user_data.clear()
        context.user_data['to_delete'] = to_del
        if msg_to_send:
            context.user_data["msg_to_send"] = msg_to_send
        return self.start(update, context)


# ADMIN SIDE
SET_IMAGE, SET_NAME, SET_PRICE, SET_DESCRIPTION, \
    CONFIRM_ADDING, ADMIN_ORDERS_INBOX, CONFIRM_CHANGE_ORDER_STATUS, \
    ALL_PRODUCTS, CONFIRM_DELETE_PRODUCT, CONFIRM_CHANGE_PRODUCT_STATUS, \
    CONFIRM_MARK_COMPLETED, CHOOSE_BUYER, CONFIRM_SELL,\
    SET_NOT_TELEGRAM_BUYER, CONFIRM_NOT_TEL_BUYER, CONFIRM_MARK_IN_STOCK = range(16)

ADMIN_START_HANDLER = CommandHandler("a", Admin().start)

ADMIN_ORDERS_HANDLER = ConversationHandler(
    entry_points=[CallbackQueryHandler(Admin().all_orders, pattern=r"all_orders")],
    states={
        ADMIN_ORDERS_INBOX: [CallbackQueryHandler(Admin().all_orders, pattern="^[0-9]+$"),
                             # CallbackQueryHandler(Admin().confirm_mark_as_completed,
                             #                      pattern=r"mark_as_completed"),
                             # CallbackQueryHandler(Admin().delete_order, pattern=r"delete_order")
                             ],

        # CONFIRM_MARK_COMPLETED: [  # CallbackQueryHandler(Admin().finish_mark_as_completed,
        #     #                      pattern=r"finish_mark_as_completed"),
        #     CallbackQueryHandler(Admin().all_orders,
        #                          pattern=r"back_to_all_orders")]
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
                       # CallbackQueryHandler(Admin().confirm_change_product_status, pattern=r"change_product_status")
                       CallbackQueryHandler(Admin().choose_buyer, pattern=r"mark_as_sold"),
                       CallbackQueryHandler(Admin().confirm_mark_as_in_stock, pattern=r"mark_as_in_stock")
                       ],

        CONFIRM_DELETE_PRODUCT: [CallbackQueryHandler(Admin().finish_delete_product, pattern=r"delete_product"),
                                 CallbackQueryHandler(Admin().all_products, pattern=r"back_to_all_products")],

        # CONFIRM_CHANGE_PRODUCT_STATUS: [  # CallbackQueryHandler(Admin().finish_change_product_status,
        #     #                    pattern=r"confirm_change_product_status"),
        #                                 CallbackQueryHandler(Admin().all_products,
        #                                                      pattern=r"back_to_all_products")],

        CHOOSE_BUYER: [CallbackQueryHandler(Admin().all_products, pattern="^[0-9]+$"),
                       CallbackQueryHandler(Admin().confirm_sell, pattern=r"select_order"),
                       CallbackQueryHandler(Admin().finish_sell_not_tel, pattern=r"set_not_telegram_buyer")],

        CONFIRM_SELL: [CallbackQueryHandler(Admin().finish_sell, pattern=r"finish_sell"),
                       CallbackQueryHandler(Admin().all_products, pattern=r"back_to_all_products")],

        CONFIRM_MARK_IN_STOCK: [CallbackQueryHandler(Admin().put_in_stock, pattern=r"mark_as_in_stock"),
                                CallbackQueryHandler(Admin().all_products, pattern=r"back_to_all_products")]

        # SET_NOT_TELEGRAM_BUYER: [MessageHandler(Filters.text, Admin().confirm_sell_not_tel_buyer),
        #                          CallbackQueryHandler(Admin().all_products, pattern=r"back_to_all_products")],

        # CONFIRM_NOT_TEL_BUYER: [CallbackQueryHandler(Admin().finish_sell, pattern=r"finish_sell"),
        #                         CallbackQueryHandler(Admin().all_products, pattern=r"back_to_all_products")]
    },
    fallbacks=[CallbackQueryHandler(Admin().back_to_main_menu, pattern=r"back_to_admin_main_menu")]
)
