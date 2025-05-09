# Copyright ©️ 2025 THEETOX
"""
Payment Handlers Module
Handles payment processing for premium features like unlocking trading and CMC listing.
"""

import os
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from Utils.BlockChain import unlock_trading, submit_cmc, verify_payment
from Utils.Database import get_user_coin, update_coin_status

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration from environment
DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")
PAYMENT_WALLET = os.getenv("PAYMENT_WALLET")

# Pricing in BNB
UNLOCK_PRICE = 0.05
CMC_PRICE = 0.5

async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /unlock command to enable trading for a coin.
    """
    user_id = update.effective_user.id
    
    # Check if user has a coin
    coin = get_user_coin(user_id)
    if not coin:
        await update.message.reply_text(
            "❌ You don't have any coins created yet. Use /createfree to create one first."
        )
        return
    
    # Check if trading is already enabled
    if coin['trading_enabled']:
        await update.message.reply_text(
            f"✅ Trading is already enabled for your coin {coin['name']} ({coin['symbol']})."
        )
        return
    
    # Create payment instructions
    payment_address = PAYMENT_WALLET
    payment_amount = UNLOCK_PRICE
    
    # Create a unique payment reference
    payment_ref = f"UNLOCK-{coin['ref_id']}"
    
    # Create inline keyboard with payment options
    keyboard = [
        [InlineKeyboardButton("💳 Pay with TON Connect", callback_data=f"ton_pay_unlock_{coin['contract_address']}")],
        [InlineKeyboardButton("✅ I've Sent the Payment", callback_data=f"verify_unlock_{coin['contract_address']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔓 *Unlock Trading for {coin['name']} ({coin['symbol']})*\n\n"
        f"To enable trading for your coin, please send *{payment_amount} BNB* to:\n\n"
        f"`{payment_address}`\n\n"
        f"*Important:*\n"
        f"- Include reference: `{payment_ref}` in transaction memo\n"
        f"- Only BNB on Binance Smart Chain (BSC) is accepted\n\n"
        f"After sending the payment, click 'I've Sent the Payment' to verify.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def cmc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /cmc command to submit for CMC listing.
    """
    user_id = update.effective_user.id
    
    # Check if user has a coin
    coin = get_user_coin(user_id)
    if not coin:
        await update.message.reply_text(
            "❌ You don't have any coins created yet. Use /createfree to create one first."
        )
        return
    
    # Check if trading is enabled (required for CMC)
    if not coin['trading_enabled']:
        await update.message.reply_text(
            f"❌ Trading must be enabled before submitting to CMC.\n"
            f"Use /unlock to enable trading for your coin first."
        )
        return
    
    # Check if already submitted to CMC
    if coin.get('cmc_submitted', False):
        await update.message.reply_text(
            f"✅ Your coin {coin['name']} ({coin['symbol']}) has already been submitted to CMC."
        )
        return
    
    # Create payment instructions
    payment_address = PAYMENT_WALLET
    payment_amount = CMC_PRICE
    
    # Create a unique payment reference
    payment_ref = f"CMC-{coin['ref_id']}"
    
    # Create inline keyboard with payment options
    keyboard = [
        [InlineKeyboardButton("💳 Pay with TON Connect", callback_data=f"ton_pay_cmc_{coin['contract_address']}")],
        [InlineKeyboardButton("✅ I've Sent the Payment", callback_data=f"verify_cmc_{coin['contract_address']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📊 *CMC Listing for {coin['name']} ({coin['symbol']})*\n\n"
        f"To submit your coin to CoinMarketCap, please send *{payment_amount} BNB* to:\n\n"
        f"`{payment_address}`\n\n"
        f"*Important:*\n"
        f"- Include reference: `{payment_ref}` in transaction memo\n"
        f"- Only BNB on Binance Smart Chain (BSC) is accepted\n\n"
        f"After sending the payment, click 'I've Sent the Payment' to verify.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def handle_ton_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle TON Connect payment callback.
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    # Extract payment type and contract address
    parts = data.split('_')
    payment_type = parts[2]  # unlock or cmc
    contract_address = parts[3]
    
    # Get coin details
    coin = get_user_coin(user_id)
    if not coin or coin['contract_address'] != contract_address:
        await query.edit_message_text(
            "❌ Invalid coin or contract address. Please try again."
        )
        return
    
    # Determine payment amount
    payment_amount = UNLOCK_PRICE if payment_type == "unlock" else CMC_PRICE
    
    # Generate TON Connect payment link (simplified for this example)
    ton_payment_link = f"https://tonconnect.example.com/pay?address={PAYMENT_WALLET}&amount={payment_amount}&memo={payment_type.upper()}-{coin['ref_id']}"
    
    # Create inline keyboard with payment link
    keyboard = [
        [InlineKeyboardButton("💰 Pay with TON", url=ton_payment_link)],
        [InlineKeyboardButton("✅ I've Completed Payment", callback_data=f"verify_{payment_type}_{contract_address}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💳 *TON Connect Payment*\n\n"
        f"Please complete the payment of *{payment_amount} BNB* using TON Connect.\n\n"
        f"After completing the payment, click 'I've Completed Payment' to verify.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def verify_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Verify payment and process the requested action.
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    # Extract payment type and contract address
    parts = data.split('_')
    payment_type = parts[1]  # unlock or cmc
    contract_address = parts[2]
    
    # Get coin details
    coin = get_user_coin(user_id)
    if not coin or coin['contract_address'] != contract_address:
        await query.edit_message_text(
            "❌ Invalid coin or contract address. Please try again."
        )
        return
    
    # Show verifying message
    await query.edit_message_text(
        f"⏳ Verifying your payment... This may take a moment."
    )
    
    # Determine payment amount and reference
    payment_amount = UNLOCK_PRICE if payment_type == "unlock" else CMC_PRICE
    payment_ref = f"{payment_type.upper()}-{coin['ref_id']}"
    
    # Verify payment on blockchain
    payment_verified = await verify_payment(
        wallet_address=PAYMENT_WALLET,
        expected_amount=payment_amount,
        reference=payment_ref
    )
    
    if not payment_verified:
        # Payment not found or insufficient
        keyboard = [
            [InlineKeyboardButton("💳 Try Again", callback_data=f"ton_pay_{payment_type}_{contract_address}")],
            [InlineKeyboardButton("❓ Need Help", url="https://t.me/memecoin_support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ Payment verification failed.\n\n"
            f"Possible reasons:\n"
            f"- Payment not received yet (blockchain confirmations can take time)\n"
            f"- Incorrect payment amount (expected {payment_amount} BNB)\n"
            f"- Missing or incorrect reference in transaction memo\n\n"
            f"Please try again or contact support if you need assistance.",
            reply_markup=reply_markup
        )
        return
    
    # Payment verified, process the action
    try:
        if payment_type == "unlock":
            # Enable trading
            success = await unlock_trading(
                contract_address=contract_address,
                deployer_key=DEPLOYER_PRIVATE_KEY
            )
            
            if success:
                # Update database
                update_coin_status(user_id, contract_address, trading_enabled=True)
                
                # Send success message
                bscscan_url = f"https://bscscan.com/token/{contract_address}"
                
                keyboard = [
                    [InlineKeyboardButton("🔍 View on BSCScan", url=bscscan_url)],
                    [InlineKeyboardButton("📊 CMC Listing (0.5 BNB)", callback_data=f"ton_pay_cmc_{contract_address}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ *Trading Unlocked Successfully!*\n\n"
                    f"Your coin {coin['name']} ({coin['symbol']}) is now tradeable!\n\n"
                    f"Contract: `{contract_address}`\n\n"
                    f"You can now add liquidity and start trading your coin.\n"
                    f"Consider submitting to CoinMarketCap for more visibility!",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            else:
                raise Exception("Failed to enable trading")
                
        elif payment_type == "cmc":
            # Submit to CMC
            success = await submit_cmc(
                name=coin['name'],
                symbol=coin['symbol'],
                contract_address=contract_address,
                logo_path=coin['logo_path']
            )
            
            if success:
                # Update database
                update_coin_status(user_id, contract_address, cmc_submitted=True)
                
                # Send success message
                await query.edit_message_text(
                    f"✅ *CMC Listing Submission Successful!*\n\n"
                    f"Your coin {coin['name']} ({coin['symbol']}) has been submitted to CoinMarketCap!\n\n"
                    f"The CMC team will review your submission, which typically takes 5-7 business days.\n\n"
                    f"You'll receive an email notification when your coin is listed.\n\n"
                    f"Thank you for using our service!",
                    parse_mode="Markdown"
                )
            else:
                raise Exception("Failed to submit to CMC")
                
    except Exception as e:
        logger.error(f"Error processing {payment_type} for {contract_address}: {e}")
        
        await query.edit_message_text(
            f"❌ Error processing your request: {str(e)}\n\n"
            f"Your payment has been verified, but there was an error processing your {payment_type} request.\n\n"
            f"Please contact support for assistance."
        )

def setup_payment_handlers(application: Application) -> None:
    """
    Set up all handlers related to payments.
    """
    # Add command handlers
    application.add_handler(CommandHandler("unlock", unlock_command))
    application.add_handler(CommandHandler("cmc", cmc_command))
    
    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(handle_ton_payment, pattern=r"^ton_pay_"))
    application.add_handler(CallbackQueryHandler(verify_payment_callback, pattern=r"^verify_"))
