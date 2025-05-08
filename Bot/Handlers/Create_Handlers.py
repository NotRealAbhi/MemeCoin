# Copyright ©️ 2025 THEETOX
"""
Create Handlers Module
Handles the coin creation process and related commands.
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
from utils.image_processor import compress_image
from utils.blockchain import deploy_contract
from utils.database import add_new_coin, get_user_coin
import random
import string

# States for conversation handler
(NAME, SYMBOL, SUPPLY, LOGO, CONFIRM) = range(5)

# User session storage
user_data = {}

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration from environment
DEV_WALLET = os.getenv("DEV_WALLET")
MARKETING_WALLET = os.getenv("MARKETING_WALLET")
LIQUIDITY_WALLET = os.getenv("LIQUIDITY_WALLET")
DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")

async def create_free(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the free coin creation process.
    """
    user_id = update.effective_user.id
    
    # Check if user already has a coin
    existing_coin = get_user_coin(user_id)
    if existing_coin:
        await update.message.reply_text(
            f"⚠️ You already have a coin: {existing_coin['name']} ({existing_coin['symbol']})\n"
            f"Contract: {existing_coin['contract_address']}\n\n"
            f"You can only create one coin per Telegram account."
        )
        return ConversationHandler.END
    
    # Initialize user data
    user_data[user_id] = {}
    
    await update.message.reply_text(
        "🚀 Let's create your memecoin!\n\n"
        "First, what's the name of your coin?\n"
        "(e.g., 'Doge Coin', 'Shiba Inu', etc.)"
    )
    
    return NAME

async def coin_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process the coin name and ask for symbol.
    """
    user_id = update.effective_user.id
    name = update.message.text.strip()
    
    # Validate name
    if len(name) < 3 or len(name) > 30:
        await update.message.reply_text(
            "⚠️ Coin name must be between 3 and 30 characters.\n"
            "Please enter a valid name:"
        )
        return NAME
    
    # Store name
    user_data[user_id]['name'] = name
    
    await update.message.reply_text(
        f"Great! Your coin will be named '{name}'.\n\n"
        f"Now, what's the symbol for your coin?\n"
        f"(e.g., 'DOGE', 'SHIB', etc. - 2-6 characters)"
    )
    
    return SYMBOL

async def coin_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process the coin symbol and ask for supply.
    """
    user_id = update.effective_user.id
    symbol = update.message.text.strip().upper()
    
    # Validate symbol
    if len(symbol) < 2 or len(symbol) > 6 or not symbol.isalnum():
        await update.message.reply_text(
            "⚠️ Symbol must be 2-6 alphanumeric characters.\n"
            "Please enter a valid symbol:"
        )
        return SYMBOL
    
    # Store symbol
    user_data[user_id]['symbol'] = symbol
    
    # Ask for total supply with buttons for common options
    keyboard = [
        [InlineKeyboardButton("1,000,000", callback_data="supply_1000000")],
        [InlineKeyboardButton("100,000,000", callback_data="supply_100000000")],
        [InlineKeyboardButton("1,000,000,000", callback_data="supply_1000000000")],
        [InlineKeyboardButton("Custom Supply", callback_data="supply_custom")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Your coin will be {user_data[user_id]['name']} ({symbol}).\n\n"
        f"Now, what's the total supply for your coin?",
        reply_markup=reply_markup
    )
    
    return SUPPLY

async def supply_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process supply selection from buttons.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "supply_custom":
        await query.edit_message_text(
            "Please enter your custom supply (number only):\n"
            "Example: 1000000000"
        )
        return SUPPLY
    
    # Extract supply from callback data
    supply = int(data.split("_")[1])
    user_data[user_id]['supply'] = supply
    
    await query.edit_message_text(
        f"Great! Your coin will have a total supply of {supply:,}.\n\n"
        f"Now, please upload a logo for your coin (square image, will be resized to 512x512)."
    )
    
    return LOGO

async def custom_supply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process custom supply input.
    """
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    try:
        supply = int(text.replace(',', ''))
        if supply <= 0 or supply > 1000000000000000:  # 1 quadrillion max
            raise ValueError("Supply out of range")
    except ValueError:
        await update.message.reply_text(
            "⚠️ Please enter a valid number for the supply.\n"
            "Example: 1000000000"
        )
        return SUPPLY
    
    # Store supply
    user_data[user_id]['supply'] = supply
    
    await update.message.reply_text(
        f"Great! Your coin will have a total supply of {supply:,}.\n\n"
        f"Now, please upload a logo for your coin (square image, will be resized to 512x512)."
    )
    
    return LOGO

async def coin_logo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process the coin logo upload.
    """
    user_id = update.effective_user.id
    
    # Check if a photo was uploaded
    if not update.message.photo:
        await update.message.reply_text(
            "⚠️ Please upload an image file for your coin logo."
        )
        return LOGO
    
    # Get the largest photo (best quality)
    photo = update.message.photo[-1]
    photo_file = await context.bot.get_file(photo.file_id)
    
    # Download and process the image
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Compress and resize the image
    try:
        compressed_logo = compress_image(photo_bytes)
        
        # Save the logo to user data
        logo_filename = f"{user_id}_{user_data[user_id]['symbol']}.png"
        logo_path = os.path.join("logos", logo_filename)
        
        # Ensure the logos directory exists
        os.makedirs("logos", exist_ok=True)
        
        # Save the compressed image
        with open(logo_path, "wb") as f:
            f.write(compressed_logo)
        
        user_data[user_id]['logo_path'] = logo_path
        
        # Show confirmation with all details
        name = user_data[user_id]['name']
        symbol = user_data[user_id]['symbol']
        supply = user_data[user_id]['supply']
        
        # Send the processed logo back to the user
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=compressed_logo,
            caption=f"✅ Logo processed successfully!\n\n"
                   f"*Coin Details:*\n"
                   f"Name: {name}\n"
                   f"Symbol: {symbol}\n"
                   f"Supply: {supply:,}\n\n"
                   f"Is this correct? If yes, I'll deploy your coin!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, deploy my coin!", callback_data="confirm_yes")],
                [InlineKeyboardButton("❌ No, start over", callback_data="confirm_no")]
            ])
        )
        
        return CONFIRM
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text(
            "❌ There was an error processing your image. Please try uploading a different image."
        )
        return LOGO

async def confirm_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Confirm coin creation and deploy the contract.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "confirm_no":
        await query.edit_message_caption(
            caption="🔄 Coin creation cancelled. Use /createfree to start over."
        )
        return ConversationHandler.END
    
    # Get coin details
    name = user_data[user_id]['name']
    symbol = user_data[user_id]['symbol']
    supply = user_data[user_id]['supply']
    logo_path = user_data[user_id]['logo_path']
    
    # Show deploying message
    await query.edit_message_caption(
        caption=f"⏳ Deploying your coin...\n\n"
               f"Name: {name}\n"
               f"Symbol: {symbol}\n"
               f"Supply: {supply:,}\n\n"
               f"This may take a minute or two. Please wait.",
        parse_mode="Markdown"
    )
    
    try:
        # Generate a random reference ID for this deployment
        ref_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Deploy the contract
        contract_address = await deploy_contract(
            name=name,
            symbol=symbol,
            total_supply=supply,
            dev_wallet=DEV_WALLET,
            marketing_wallet=MARKETING_WALLET,
            liquidity_wallet=LIQUIDITY_WALLET,
            deployer_key=DEPLOYER_PRIVATE_KEY
        )
        
        if not contract_address:
            raise Exception("Contract deployment failed")
        
        # Save to database
        add_new_coin(
            user_id=user_id,
            name=name,
            symbol=symbol,
            supply=supply,
            logo_path=logo_path,
            contract_address=contract_address,
            ref_id=ref_id,
            trading_enabled=False
        )
        
        # Send success message
        bscscan_url = f"https://bscscan.com/token/{contract_address}"
        
        # Create inline keyboard with options
        keyboard = [
            [InlineKeyboardButton("🔍 View on BSCScan", url=bscscan_url)],
            [InlineKeyboardButton("🔓 Unlock Trading (0.05 BNB)", callback_data=f"unlock_{contract_address}")],
            [InlineKeyboardButton("📊 CMC Listing (0.5 BNB)", callback_data=f"cmc_{contract_address}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(logo_path, "rb"),
            caption=f"🆓 FREE COIN CREATED!\n\n"
                   f"Name: {name} ({symbol})\n"
                   f"Contract: `{contract_address}`\n"
                   f"Reference ID: {ref_id}\n\n"
                   f"❌ TRADING LOCKED - Pay 0.05 BNB to unlock\n\n"
                   f"Use /unlock to enable trading\n"
                   f"Use /cmc for CMC listing submission",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        # Clean up user data
        if user_id in user_data:
            del user_data[user_id]
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error deploying contract: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ There was an error deploying your coin: {str(e)}\n"
                 f"Please try again later or contact support."
        )
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel the conversation.
    """
    user_id = update.effective_user.id
    
    # Clean up user data
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text(
        "❌ Coin creation cancelled. Use /createfree to start over."
    )
    
    return ConversationHandler.END

def setup_create_handlers(application: Application) -> None:
    """
    Set up all handlers related to coin creation.
    """
    # Create conversation handler for coin creation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("createfree", create_free)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, coin_name)],
            SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, coin_symbol)],
            SUPPLY: [
                CallbackQueryHandler(supply_button, pattern=r"^supply_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, custom_supply)
            ],
            LOGO: [MessageHandler(filters.PHOTO, coin_logo)],
            CONFIRM: [CallbackQueryHandler(confirm_creation, pattern=r"^confirm_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    application.add_handler(conv_handler)
