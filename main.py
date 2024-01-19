import logging
from collections import OrderedDict
from operator import itemgetter
from uuid import uuid4

import telegram.error
from telegram import *
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import *

from db.Database import Database
from db.Database import Table
from db.Database import Column
from db import utils
import structures

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

NO_REFEREES = {"no_referees": 0}

subscription_requirement_chat_ids = [-1002052097788, -1002115859556]

waiting_for_message = False
waiting_for_button_title = False
waiting_for_button_url = False
message: Message = Message(message_id=Message.message_id, chat=Message.chat, date=Message.date)
message_keyboard: list[list[InlineKeyboardButton]] = []
button_title = ""
button_url = ""

db_columns = (Column("id", int, False),
              Column("name", str, False),
              Column("is_subscribed", bool, False),
              Column("referrer", int, False),
              Column("referees", int, False),
              Column("serial", int, True))
db_columns_presale = (Column("id", int, True),
                      Column("nft_balance", int, False))

database = Database("database.db")

users_table = Table("users", db_columns)
presale_table = Table("presale", db_columns_presale)


def reset_message_variables() -> None:
    global waiting_for_message, waiting_for_button_title, waiting_for_button_url, \
        message, message_keyboard, button_title, button_url
    waiting_for_message = False
    waiting_for_button_title = False
    waiting_for_button_url = False
    message = None
    message_keyboard = []
    button_title = ""
    button_url = ""


def get_referee_number(user_id) -> int:
    global users_table, db_columns
    referee_rows = database.query(users_table, (db_columns[0],),
                                  {db_columns[3]: user_id},
                                  [utils.OPERATORS['is']], False)
    return len(referee_rows)


def get_top_referrers(user_id) -> dict:
    global users_table, db_columns
    user_rows = database.query(users_table, (db_columns[1], db_columns[4]),
                               {db_columns[3]: int(user_id)},
                               [utils.OPERATORS['is']], False)

    if len(user_rows) == 0:
        return NO_REFEREES

    referee_numbers = {}
    for user_row in user_rows:
        referee_numbers[user_row[0]] = user_row[1]

    return dict(sorted(referee_numbers.items(), key=itemgetter(1), reverse=True)[:10])


def get_rank(user_id: int, corrected: bool) -> int:
    global users_table, db_columns
    user_rows = database.query(users_table, (db_columns[0], db_columns[4], db_columns[5]),
                               utils.NO_CONDITION,
                               utils.NO_OPERATOR, False)

    base_ranks = {}
    for user_row in user_rows:
        base_ranks[user_row[0]] = user_row[2]
    sorted_base_ranks = OrderedDict(sorted(base_ranks.items(), key=itemgetter(1), reverse=False))

    if not corrected:
        return OrderedDict(sorted(base_ranks.items(), key=itemgetter(1), reverse=True))[user_id]

    referee_numbers = {}
    for user_row in user_rows:
        referee_numbers[user_row[0]] = user_row[1]
    sorted_referee_numbers = OrderedDict(sorted(referee_numbers.items(), key=itemgetter(1), reverse=True))

    ranks = []

    for user in sorted_referee_numbers.keys():
        # get all keys that have the value of the current user's referee number
        same_referee_number = [k for k, v in sorted_referee_numbers.items() if v == sorted_referee_numbers[user]]
        if len(same_referee_number) == 1:
            if user not in ranks:
                ranks.append(user)
        else:
            same_referee_number_base_ranks = {}
            for repeated_user in same_referee_number:
                same_referee_number_base_ranks.update({repeated_user: sorted_base_ranks[repeated_user]})
            sorted_same_referee_number_base_ranks = OrderedDict(
                sorted(same_referee_number_base_ranks.items(), key=itemgetter(1), reverse=False))
            for repeated_user in sorted_same_referee_number_base_ranks.keys():
                if repeated_user not in ranks:
                    ranks.append(repeated_user)

    return ranks.index(user_id) + 1


def get_nft_numbers(update: Update) -> tuple[int, int, int]:
    global users_table, db_columns_presale
    nft_balance = database.query(presale_table, (db_columns_presale[1],),
                                 {db_columns_presale[0]: update.effective_user.id},
                                 [utils.OPERATORS['is']], False)[0][0]
    total_nft, total_nft_bought = get_nft_status()
    return nft_balance, total_nft, total_nft_bought


def get_nft_status() -> tuple[int, int]:
    global users_table, db_columns_presale
    total_nft = database.query(presale_table, (db_columns_presale[1],),
                               {db_columns_presale[0]: -1},
                               [utils.OPERATORS['is']], False)[0][0]
    total_nft_bought = database.query(presale_table, (db_columns_presale[1],),
                                      {db_columns_presale[0]: -1},
                                      [utils.OPERATORS['not']], True)[0][0]
    return total_nft, total_nft_bought


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int) -> None:
    global database, db_columns
    user_id = update.effective_user.id
    await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=message_id)
    await context.bot.sendPhoto(
        caption=structures.get_menu_text(get_rank(user_id, False), get_referee_number(user_id), user_id),
        photo="https://i.imgur.com/dPIBptY.jpg",
        chat_id=update.effective_chat.id,
        reply_markup=structures.get_menu_keyboard(user_id),
        parse_mode=ParseMode.HTML)


async def show_presale_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int) -> None:
    nft_balance, total_nft, total_nft_bought = get_nft_numbers(update)
    await context.bot.edit_message_text(
        text=structures.get_presale_text(nft_balance, total_nft, total_nft_bought),
        chat_id=update.effective_chat.id,
        message_id=message_id,
        reply_markup=structures.get_presale_keyboard(),
        parse_mode=ParseMode.HTML)


async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int) -> None:
    await context.bot.edit_message_text(
        text=structures.admin_panel_text,
        chat_id=update.effective_chat.id,
        message_id=message_id,
        reply_markup=structures.get_admin_panel_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def presale_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    nft_balance, total_nft, total_nft_bought = get_nft_numbers(update)
    await context.bot.send_message(
        text=structures.get_presale_text(nft_balance, total_nft, total_nft_bought),
        chat_id=update.effective_chat.id,
        reply_markup=structures.get_presale_keyboard(),
        parse_mode=ParseMode.HTML)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global database, db_columns, db_columns_presale
    status_channel = (await context.bot.getChatMember(subscription_requirement_chat_ids[0],
                                                      update.effective_user.id)).status
    if status_channel == ChatMemberStatus.ADMINISTRATOR or status_channel == ChatMemberStatus.OWNER:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=structures.admin_panel_text,
                                       reply_markup=structures.get_admin_panel_keyboard())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global users_table, presale_table, db_columns, db_columns_presale
    ref_id = context.args
    user_row = database.query(users_table, (db_columns[0],),
                              {db_columns[0]: update.effective_user.id},
                              [utils.OPERATORS['is']], False)
    if not len(user_row):
        if len(ref_id) and not int(ref_id[0]) == update.effective_user.id:
            database.insert(users_table, {db_columns[0]: update.effective_chat.id,
                                          db_columns[1]: update.effective_user.full_name,
                                          db_columns[2]: False, db_columns[3]: int(ref_id[0]),
                                          db_columns[4]: 0, db_columns[5]: database.count_rows(users_table)[0] + 1})
            referee_rows = database.query(users_table, (db_columns[0],),
                                          {db_columns[3]: int(ref_id[0])},
                                          [utils.OPERATORS['is']], False)
            if referee_rows is not None:
                database.update(users_table, {db_columns[4]: len(referee_rows)},
                                {db_columns[0]: int(ref_id[0])})
        else:
            database.insert(users_table, {db_columns[0]: update.effective_chat.id,
                                          db_columns[1]: update.effective_user.full_name,
                                          db_columns[2]: False, db_columns[3]: -1,
                                          db_columns[4]: 0, db_columns[5]: database.count_rows(users_table)[0] + 1})
        database.insert(presale_table, {db_columns_presale[0]: update.effective_chat.id,
                                        db_columns_presale[1]: 0})

        await context.bot.send_message(chat_id=update.effective_chat.id, text=structures.welcome_message)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=structures.subscription_check_message,
                                       reply_markup=structures.get_subscription_check_keyboard(),
                                       parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=structures.restart_message,
                                       reply_markup=structures.get_return_to_menu_keyboard())


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global subscription_requirement_chat_ids, users_table, presale_table, db_columns, \
        waiting_for_message, waiting_for_button_title, waiting_for_button_url, \
        message, message_keyboard
    query = update.callback_query
    await query.answer()
    if query.data == "subscription_check":
        status_channel = (await context.bot.getChatMember(subscription_requirement_chat_ids[0],
                                                          update.effective_user.id)).status
        status_community = (await context.bot.getChatMember(subscription_requirement_chat_ids[1],
                                                            update.effective_user.id)).status
        if (status_channel == ChatMemberStatus.MEMBER or
            status_channel == ChatMemberStatus.ADMINISTRATOR or
            status_channel == ChatMemberStatus.OWNER) and \
                (status_community == ChatMemberStatus.MEMBER or
                 status_community == ChatMemberStatus.ADMINISTRATOR or
                 status_community == ChatMemberStatus.OWNER):
            database.update(users_table, {db_columns[2]: True}, {db_columns[0]: query.from_user.id})
            await show_menu(update, context, query.message.message_id)
        else:
            await context.bot.edit_message_text(text=structures.not_subscribed_message,
                                                chat_id=update.effective_chat.id,
                                                message_id=query.message.message_id,
                                                reply_markup=structures.get_subscription_check_keyboard(),
                                                parse_mode=ParseMode.HTML)
            database.update(users_table, {db_columns[2]: False}, {db_columns[0]: query.from_user.id})
    if query.data == "ref_dashboard":
        user_id = update.effective_user.id
        await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=query.message.message_id)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=structures.get_ref_dashboard_text(get_referee_number(user_id),
                                                                              user_id),
                                       reply_markup=structures.get_return_to_menu_keyboard(),
                                       parse_mode=ParseMode.HTML)
    if query.data == "whitelist_presale":
        await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=query.message.message_id)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=structures.presale_standby_text,
                                       reply_markup=structures.get_return_to_menu_keyboard(),
                                       parse_mode=ParseMode.HTML)
    if query.data == "buy_nft":
        await context.bot.edit_message_text(text=structures.buying_text,
                                            chat_id=update.effective_chat.id,
                                            message_id=query.message.message_id,
                                            reply_markup=structures.get_buying_keyboard())
    if query.data == "about":
        await context.bot.edit_message_text(
            text=structures.about_text,
            chat_id=update.effective_chat.id,
            message_id=query.message.message_id,
            reply_markup=structures.get_return_to_presale_keyboard()
        )
    if query.data == "return_to_presale":
        await context.bot.edit_message_text(text=structures.presale_loading_message,
                                            chat_id=update.effective_chat.id,
                                            message_id=query.message.message_id,
                                            reply_markup=structures.get_presale_keyboard(),
                                            parse_mode=ParseMode.HTML)
        await show_presale_message(update, context, query.message.id)
    if query.data == "return_to_menu":
        await show_menu(update, context, query.message.message_id)
    if query.data == "admin_statistics":
        await context.bot.edit_message_text(text=structures.admin_statistics_loading_text,
                                            chat_id=update.effective_chat.id,
                                            message_id=query.message.message_id,
                                            reply_markup=structures.get_admin_statistics_keyboard())
        total_users = len(database.query(users_table, (db_columns[0],),
                                         utils.NO_CONDITION,
                                         utils.NO_OPERATOR, False))
        total_users_subscribed = len(database.query(users_table, (db_columns[0],),
                                                    {db_columns[2]: True},
                                                    utils.OPERATORS['is'], False))
        total_nft, total_nft_bought = get_nft_status()
        await context.bot.edit_message_text(text=structures.get_admin_statistics_text(total_users,
                                                                                      total_users_subscribed,
                                                                                      total_nft_bought,
                                                                                      total_nft),
                                            chat_id=update.effective_chat.id,
                                            message_id=query.message.message_id,
                                            reply_markup=structures.get_admin_statistics_keyboard())
    if query.data == "admin_send_message":
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=structures.admin_send_message_text)
        waiting_for_message = True
    if query.data == "admin_message_confirmation_yes":
        if button_title:
            message_keyboard.append([InlineKeyboardButton(button_title, url=button_url)])
        await context.bot.edit_message_text(text=structures.admin_message_button_question,
                                            chat_id=update.effective_chat.id,
                                            message_id=query.message.message_id,
                                            reply_markup=structures.get_admin_button_question_keyboard())
    if query.data == "admin_message_confirmation_retry":
        await context.bot.edit_message_text(text=structures.admin_send_message_text,
                                            chat_id=update.effective_chat.id,
                                            message_id=query.message.message_id)
        waiting_for_button_title = True
    if query.data == "admin_message_button_add":
        await context.bot.edit_message_text(text=structures.admin_message_button_title_question,
                                            chat_id=update.effective_chat.id,
                                            message_id=query.message.message_id)
        waiting_for_button_title = True
    if query.data == "admin_message_confirmation_send":
        await message.copy(chat_id=update.effective_chat.id, reply_markup=InlineKeyboardMarkup(message_keyboard))
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=structures.admin_message_confirmation_send_text,
                                       reply_markup=structures.get_admin_message_confirmation_send_keyboard())
    if query.data == "admin_send_message_confirmed":
        user_rows = database.query(users_table, (db_columns[0],), utils.NO_CONDITION,
                                   utils.NO_OPERATOR, False)
        for user in user_rows:
            try:
                await message.copy(chat_id=user[0], reply_markup=InlineKeyboardMarkup(message_keyboard))
            except telegram.error.Forbidden:
                print(f"User {user[0]} is unavailable.")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=structures.messages_sent_text)
        await admin_panel(update, context)
        reset_message_variables()
    if query.data == "admin_message_button_title_confirmation_yes":
        await context.bot.edit_message_text(text=structures.admin_message_button_url_question,
                                            chat_id=update.effective_chat.id,
                                            message_id=query.message.message_id)
        waiting_for_button_url = True
    if query.data == "admin_message_button_title_confirmation_retry":
        await context.bot.edit_message_text(text=structures.admin_message_button_title_question,
                                            chat_id=update.effective_chat.id,
                                            message_id=query.message.message_id)
        waiting_for_button_title = True
    if query.data == "admin_message_button_url_confirmation_retry":
        await context.bot.edit_message_text(text=structures.admin_message_button_url_question,
                                            chat_id=update.effective_chat.id,
                                            message_id=query.message.message_id)
        waiting_for_button_url = True
    if query.data == "return_to_admin_panel":
        reset_message_variables()
        await show_admin_panel(update, context, query.message.message_id)


async def message_handler(update: Update, context: CallbackContext) -> None:
    global database, db_columns, waiting_for_message, waiting_for_button_title, \
        waiting_for_button_url, message, message_keyboard, button_title, button_url
    if waiting_for_message:
        waiting_for_message = False
        message = update.message
        await message.copy(chat_id=update.effective_chat.id)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=structures.admin_message_text_confirmation,
                                       reply_markup=structures.get_admin_message_confirmation_keyboard())
    if waiting_for_button_title:
        waiting_for_button_title = False
        button_title = update.message.text
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=structures.get_admin_message_button_title_confirmation(update.message.text),
                                       reply_markup=structures.get_admin_message_button_title_confirmation_keyboard())
    if waiting_for_button_url:
        waiting_for_button_url = False
        button_url = update.message.text
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=structures.get_admin_message_button_url_confirmation(button_url),
                                       reply_markup=structures.get_admin_message_button_url_confirmation_keyboard())


async def inline_handler(update: Update, context: CallbackContext) -> None:
    global database, db_columns, users_table
    query = update.inline_query.query

    if not query:
        return

    user_row = database.query(users_table, (db_columns[0],),
                              {db_columns[0]: update.effective_user.id, db_columns[2]: True},
                              [utils.OPERATORS['is'], utils.OPERATORS['is']], False)

    if not len(user_row):
        return

    results = [
        InlineQueryResultPhoto(
            id=str(uuid4()),
            title="Share Referral Link",
            photo_url="https://i.imgur.com/dPIBptY.jpg",
            caption=structures.get_referral_link_message_text(update.effective_user.id),
            parse_mode=ParseMode.HTML,
            thumbnail_url="https://i.imgur.com/dPIBptY.jpg")
    ]

    await update.inline_query.answer(results)


if __name__ == '__main__':
    application = ApplicationBuilder().token(structures.token).build()

    database.add_table(users_table)
    database.add_table(presale_table)
    # database.insert(presale_table, {db_columns_presale[0]: -1, db_columns_presale[1]: 2500})

    start_handler = CommandHandler('start', start)
    admin_handler = CommandHandler('admin', admin_panel)
    #   DEBUG_presale_handler = CommandHandler('presale', presale_message)
    custom_message_handler = MessageHandler(~filters.COMMAND, message_handler)
    application.add_handler(start_handler)
    #   application.add_handler(DEBUG_presale_handler)
    application.add_handler(admin_handler)
    application.add_handler(custom_message_handler)
    application.add_handler(CallbackQueryHandler(callback_handler))

    application.run_polling()
