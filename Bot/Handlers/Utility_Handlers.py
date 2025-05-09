# Copyright ©️ 2025 THEETOX 
"""
Utility Handlers Module
Handles utility commands and functions for the bot.
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from Bot.Utils.Database import get_user_coin
import openai

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# OpenAI API key for shill message generation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client if API key is available
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

async def generate_shill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Generate a shill message for the user's coin using GPT-3.5.
    """
    user_id = update.effective_user.id
    
    # Check if user has a coin
    coin = get_user_coin(user_id)
    if not coin:
        await update.message.reply_text(
            "❌ You don't have any coins created yet. Use /createfree to create one first."
        )
        return
    
    # Check if OpenAI API key is configured
    if not OPENAI_API_KEY:
        await update.message.reply_text(
            "❌ Shill message generation is currently unavailable. Please try again later."
        )
        return
    
    try:
        # Show generating message
        message = await update.message.reply_text(
            "⏳ Generating your shill message... This may take a moment."
        )
        
        # Generate shill message using GPT-3.5
        prompt = f"""Generate an enthusiastic and engaging cryptocurrency shill message for a new memecoin with the following details:
        
        Name: {coin['name']}
        Symbol: {coin['symbol']}
        Contract Address: {coin['contract_address']}
        
        The message should be attention-grabbing, mention the potential for growth, and encourage people to buy and hold.
        Include some rocket emojis 🚀 and other relevant emojis.
        Keep it under 500 characters and make it sound exciting but not scammy.
        """
        
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        shill_message = response.choices[0].text.strip()
        
        # Create copy button
        keyboard = [
            [InlineKeyboardButton("📋 Copy Message", callback_data=f"copy_shill_{coin['contract_address']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the generated shill message
        await message.edit_text(
            f"✅ *Your Shill Message:*\n\n{shill_message}\n\n"
            f"Click the button below to copy this message.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error generating shill message: {e}")
        await update.message.reply_text(
            "❌ There was an error generating your shill message. Please try again later."
        )

async def copy_shill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the copy shill message callback.
    """
    query = update.callback_query
    await query.answer("Message copied to clipboard!")
    
    # The actual copying happens on the client side when the user clicks the button
    # This just acknowledges the action

async def my_coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show information about the user's coin.
    """
    user_id = update.effective_user.id
    
    # Check if user has a coin
    coin = get_user_coin(user_id)
    if not coin:
        await update.message.reply_text(
            "❌ You don't have any coins created yet. Use /createfree to create one first."
        )
        return
    
    # Create inline keyboard with options
    keyboard = []
    
    # Add BSCScan button
    bscscan_url = f"https://bscscan.com/token/{coin['contract_address']}"
    keyboard.append([InlineKeyboardButton("🔍 View on BSCScan", url=bscscan_url)])
    
    # Add unlock trading button if not enabled
    if not coin['trading_enabled']:
        keyboard.append([InlineKeyboardButton("🔓 Unlock Trading (0.05 BNB)", callback_data=f"ton_pay_unlock_{coin['contract_address']}")])
    
    # Add CMC button if trading enabled but not submitted
    if coin['trading_enabled'] and not coin.get('cmc_submitted', False):
        keyboard.append([InlineKeyboardButton("📊 CMC Listing (0.5 BNB)", callback_data=f"ton_pay_cmc_{coin['contract_address']}")])
    
    # Add shill generator button
    keyboard.append([InlineKeyboardButton("📣 Generate Shill Message", callback_data=f"generate_shill_{coin['contract_address']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send coin information
    trading_status = "✅ ENABLED" if coin['trading_enabled'] else "❌ LOCKED"
    cmc_status = "✅ SUBMITTED" if coin.get('cmc_submitted', False) else "❌ NOT SUBMITTED"
    
    await update.message.reply_text(
        f"🪙 *Your Coin Information*\n\n"
        f"Name: {coin['name']}\n"
        f"Symbol: {coin['symbol']}\n"
        f"Contract: `{coin['contract_address']}`\n"
        f"Reference ID: {coin['ref_id']}\n\n"
        f"Trading: {trading_status}\n"
        f"CMC Listing: {cmc_status}\n\n"
        f"Use the buttons below to manage your coin:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def handle_generate_shill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the generate shill callback.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract contract address
    parts = query.data.split('_')
    contract_address = parts[2]
    
    user_id = query.from_user.id
    
    # Check if user has a coin
    coin = get_user_coin(user_id)
    if not coin or coin['contract_address'] != contract_address:
        await query.edit_message_text(
            "❌ Invalid coin or contract address. Please try again."
        )
        return
    
    # Check if OpenAI API key is configured
    if not OPENAI_API_KEY:
        await query.edit_message_text(
            "❌ Shill message generation is currently unavailable. Please try again later."
        )
        return
    
    try:
        # Show generating message
        await query.edit_message_text(
            "⏳ Generating your shill message... This may take a moment."
        )
        
        # Generate shill message using GPT-3.5
        prompt = f"""Generate an enthusiastic and engaging cryptocurrency shill message for a new memecoin with the following details:
        
        Name: {coin['name']}
        Symbol: {coin['symbol']}
        Contract Address: {coin['contract_address']}
        
        The message should be attention-grabbing, mention the potential for growth, and encourage people to buy and hold.
        Include some rocket emojis 🚀 and other relevant emojis.
        Keep it under 500 characters and make it sound exciting but not scammy.
        """
        
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        shill_message = response.choices[0].text.strip()
        
        # Create copy button
        keyboard = [
            [InlineKeyboardButton("📋 Copy Message", callback_data=f"copy_shill_{coin['contract_address']}")],
            [InlineKeyboardButton("🔙 Back to Coin Info", callback_data=f"my_coin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the generated shill message
        await query.edit_message_text(
            f"✅ *Your Shill Message:*\n\n{shill_message}\n\n"
            f"Click the button below to copy this message.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error generating shill message: {e}")
        await query.edit_message_text(
            "❌ There was an error generating your shill message. Please try again later."
        )

def setup_utility_handlers(application: Application) -> None:
    """
    Set up all utility handlers.
    """
    # Add command handlers
    application.add_handler(CommandHandler("shill", generate_shill))
    application.add_handler(CommandHandler("mycoin", my_coin))
    
    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(copy_shill, pattern=r"^copy_shill_"))
    application.add_handler(CallbackQueryHandler(handle_generate_shill, pattern=r"^generate_shill_"))
    application.add_handler(CallbackQueryHandler(my_coin, pattern=r"^my_coin$"))
