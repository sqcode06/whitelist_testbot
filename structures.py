from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import urllib.parse

token = "6413387680:AAGREejqioV_S595JCu_NnGiWriGxbQM5FU"

about_text = '''About message
text'''

admin_statistics_loading_text = '''Statistics:
Total users: ...,
Total users subscribed: ...,
Total NFT bought: ... out of ... NFT,
'''

presale_standby_text = '''
<b><u>The pre-sale has not started yet.</u></b>

Invite people, earn and win whitelist spot at the moment

If you get to whitelist here will appear the sale
'''

welcome_message = "Welcome to Glass Punks Whitelist bot!"
subscription_check_message = "Subscribe to @glasspunks and <a href=\"t.me/GlassPunksCommunity\">@GlassPunksCommunity</a> to join the whitelist bot!"
not_subscribed_message = "You are not subscribed! Please make sure to follow <a href=\"t.me/GlassPunksCommunity\">@GlassPunksCommunity</a>"
restart_message = "You have already joined the whitelist competition!"
buying_text = "Choose currency"
presale_loading_message = "Your balance: <b>... NFT</b>.\n\nAvailable <b>... from ... NFT.</b>"
admin_panel_text = "Admin panel"
admin_send_message_text = "Send me the message!"
admin_message_text_confirmation = "Is this your message?"
admin_message_button_question = "Add buttons?"
admin_message_button_title_question = "Send me the button label"
admin_message_button_url_question = "Send me the button url"
admin_message_confirmation_send_text = "Send the message?"
messages_sent_text = "Messages sent!"


def get_share_message_text(user_id: int) -> str:
    return f'''💎 Join Glass Punks Whitelist Competition and Earn

Glass Punks - a conceptual NFT art on TON. 
What you get?

- 🤑 Get access to Glass Punks pre-sale with discounted price
- 💰 Earn 10%, if your referral buys NFT

👉 https://t.me/whitelist_testbot?start={user_id}
'''


def get_referral_link_message_text(user_id: int) -> str:
    return f'''
<b><u>Join Glass Punks Whitelist Competition and Earn</u></b>

Glass Punks - a conceptual NFT art on TON. 
What you get?

- 🤑 <b>Get access to Glass Punks pre-sale with discounted price</b>
- 💰 <b>Earn 10%, if your referral buys NFT</b>

<b><a href="https://t.me/whitelist_testbot?start={user_id}">JOIN</a></b>'''


def get_presale_text(nft_balance: int, total_nft: int, total_nft_bought: int) -> str:
    return f"Your balance: <b>{nft_balance} NFT</b>.\n\nAvailable <b>{total_nft - total_nft_bought} from {total_nft} NFT.</b>"


def get_menu_text(rank: int, referees: int, user_id: int) -> str:
    return f'''
<b><u>Congratulations! You joined Glass Punks whitelist competition.</u></b>

<b>Your whitelist place - {rank}</b>

<b>Here you can earn TON and secure your pre-sale spot.</b> How? 


1. 🔝 Invite people using your referral link - increase your score to move up in the participants table - <b>TOP members will access pre-sale with discounted prices</b>

2. 💰 <b>Get 10% of NFT price</b>, If your referral buys <b>NFT</b>   


Your place in the whitelist: {rank}
People invited: {referees}

<b>Your Referral Link:</b> <code><b>https://t.me/whitelist_testbot?start={user_id}</b></code>'''


def get_ref_dashboard_text(referees: int, user_id: int) -> str:
    return f'''
People invited:  {referees}


1. Invite people using your referral link - increase your score to move up in the participants table - <b>TOP members will access pre-sale with discounted prices</b>


2. <b>Get 10% of NFT cost</b>, if person you invited buys it    

<b>Your Referral Link:</b> <code><b>https://t.me/whitelist_testbot?start={user_id}</b></code>'''


def get_admin_statistics_text(total_users: int, total_users_subscribed: int, total_nft_bought: int,
                              total_nft: int) -> str:
    return f'''Statistics:
    Total users: {total_users},
    Total users subscribed: {total_users_subscribed},
    Total NFT bought: {total_nft_bought} out of {total_nft} NFT,
    '''


def get_admin_message_button_title_confirmation(button_title: str) -> str:
    return f"Is this correct title for the button?\n\n{button_title}"


def get_admin_message_button_url_confirmation(button_url: str) -> str:
    return f"Is this correct url for the button?\n\n{button_url}"


def get_subscription_check_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('Check', callback_data="subscription_check")
    ]])


def get_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Share Referral Link',
                              url=f"https://t.me/share/url?url= &text={urllib.parse.quote(get_share_message_text(user_id))}")],
        [InlineKeyboardButton('Referral Dashboard', callback_data="ref_dashboard")],
        [InlineKeyboardButton('Whitelist Pre-Sale', callback_data="whitelist_presale")]
    ])


def get_return_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('Return to menu', callback_data="return_to_menu")
    ]])


def get_presale_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Buy NFT', callback_data="buy_nft")],
        [
            InlineKeyboardButton('About', callback_data="about"),
            InlineKeyboardButton('Refresh', callback_data="return_to_presale")
        ]
    ])


def get_buying_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Buy with USDT (TRC20/BEP20)', callback_data="usdt"),
            InlineKeyboardButton('Buy with TON', callback_data="ton")
        ],
        [InlineKeyboardButton('Return', callback_data="return_to_presale")]
    ])


def get_return_to_presale_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('Return', callback_data="return_to_presale")
    ]])


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('Statistics', callback_data="admin_statistics"),
        InlineKeyboardButton('Send message to users', callback_data="admin_send_message")
    ]])


def get_admin_statistics_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('Refresh', callback_data="admin_statistics"),
        InlineKeyboardButton('Return', callback_data="return_to_admin_panel")
    ]])


def get_admin_message_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Yes', callback_data="admin_message_confirmation_yes")],
        [InlineKeyboardButton('Retry', callback_data="admin_message_confirmation_retry")],
        [InlineKeyboardButton('Abort', callback_data="return_to_admin_panel")]
    ])


def get_admin_button_question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Add button', callback_data="admin_message_button_add")],
        [InlineKeyboardButton('Next', callback_data="admin_message_confirmation_send")]
    ])


def get_admin_message_button_title_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Yes', callback_data="admin_message_button_title_confirmation_yes")],
        [InlineKeyboardButton('Retry', callback_data="admin_message_button_title_confirmation_retry")],
        [InlineKeyboardButton('Abort', callback_data="return_to_admin_panel")]
    ])


def get_admin_message_button_url_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Yes', callback_data="admin_message_confirmation_yes")],
        [InlineKeyboardButton('Retry', callback_data="admin_message_button_url_confirmation_retry")],
        [InlineKeyboardButton('Abort', callback_data="return_to_admin_panel")]
    ])


def get_admin_message_confirmation_send_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Yes', callback_data="admin_send_message_confirmed")],
        [InlineKeyboardButton('Abort', callback_data="return_to_admin_panel")]
    ])
