"""
Memecoin Generator Bot
A Telegram bot that allows users to create and deploy memecoins on BSC.

Features:
- Create free untradeable coins
- Unlock trading for a fee
- CMC listing submission
- Logo uploads and processing
- Multi-step tokenomics setup
"""

import os
import logging
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from web3 import Web3
from PIL import Image
import io
import requests
import json
import random
import string
import asyncio

# Import handlers and utilities
from Handlers.Create_Handlers import setup_create_handlers
from Handlers.Payment_Handlers import setup_payment_handlers
from Handlers.Utility_Handlers import setup_utility_handlers
from Utils.Image_Processor import compress_image
from Utils.Blockchain import deploy_contract, unlock_trading, submit_cmc
from Utils.Database import setup_database, get_user_coin, update_coin_status

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BSC_RPC_URL = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
BSC_API_KEY = os.getenv("BSC_API_KEY")
DEV_WALLET = os.getenv("DEV_WALLET")
MARKETING_WALLET = os.getenv("MARKETING_WALLET")
LIQUIDITY_WALLET = os.getenv("LIQUIDITY_WALLET")
DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")

# Pricing in BNB
UNLOCK_PRICE = 0.05
CMC_PRICE = 0.5

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))

# User session storage
user_data = {}

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send a welcome message when the command /start is issued.
    """
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n\n"
        f"Welcome to the Memecoin Generator Bot! 🚀\n\n"
        f"I can help you create your own memecoin on Binance Smart Chain.\n\n"
        f"Commands:\n"
        f"/createfree - Create a free untradeable coin\n"
        f"/unlock - Pay 0.05 BNB to enable trading\n"
        f"/cmc - Pay 0.5 BNB for CMC listing submission\n"
        f"/help - Show this help message"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send a help message when the command /help is issued.
    """
    await update.message.reply_text(
        "🚀 *Memecoin Generator Bot Help* 🚀\n\n"
        "*Commands:*\n"
        "/createfree - Create a free untradeable coin\n"
        "/unlock - Pay 0.05 BNB to enable trading\n"
        "/cmc - Pay 0.5 BNB for CMC listing submission\n"
        "/help - Show this help message\n\n"
        "*How it works:*\n"
        "1. Use /createfree to create your coin\n"
        "2. Follow the steps to set up your tokenomics\n"
        "3. Upload a logo for your coin\n"
        "4. Get your contract deployed (trading locked)\n"
        "5. Use /unlock to enable trading for 0.05 BNB\n"
        "6. Use /cmc to submit to CoinMarketCap for 0.5 BNB\n\n"
        "*Note:* All payments are in BNB on the Binance Smart Chain.",
        parse_mode="Markdown"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Log errors caused by updates.
    """
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again later or contact support."
        )

def main() -> None:
    """
    Start the bot.
    """
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Setup database
    setup_database()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Setup module handlers
    setup_create_handlers(application)
    setup_payment_handlers(application)
    setup_utility_handlers(application)

    # Add error handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
# Copyright ©️ 2025 @THEETOX
