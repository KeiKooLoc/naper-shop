from telegram.error import TelegramError
from strings import strings
from db import products_table, orders_table
from telegram import ParseMode


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


def send_product_template(update, context, product, extra_str="", kb=None):
    image_id = product["image_id"] if product else \
        "AgADAgADa6wxG498IEjK76YtnsOl-fumhQ8ABAEAAwIAA3kAA7c9BQABFgQ"
    context.user_data['to_delete'].append(
        context.bot.send_photo(update.effective_chat.id,
                               image_id,
                               product_template(product) + extra_str,
                               reply_markup=kb,
                               parse_mode=ParseMode.MARKDOWN))

def order_template(order, product):
    user_status = "⛔ ️🚫Продан" if order["status"] else "⚠ В ожидании ️"
    return product_template(product) + \
           strings["order_template"].format(
               str(order['creation_timestamp']).split('.')[0],
               user_status)


""" 
def order_template_2(order, product):
    if orders_table.find_one({"product_id": product["_id"],
                              "status": True}):
        product_status = "Продан⛔ ️"
    else:
        product_status = "В наличии ✅"

    return strings["product_template_2"].format(
        product["name"], product["price"], product["description"], product_status) + \
           strings["order_template"].format(
               str(order['creation_timestamp']).split('.')[0],
               str(order["status"]))
"""


def admin_order_template(order, product):
    user_status = "🚫Удалён" if order["deleted_on_user_side"] else "⚠ В ожидании ️"
    extra_string = "\n_Юзер отменил заказ. Можете смело удалять запись_" \
        if order["deleted_on_user_side"] else ""

    return product_template(product) + \
           strings["admin_order_template"].format(
               order["user_mention_markdown"],
               str(order['creation_timestamp']).split('.')[0],
               user_status) + extra_string


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
