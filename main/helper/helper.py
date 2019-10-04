from telegram.error import TelegramError


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
