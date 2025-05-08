# Copyright ©️ 2025 @THEETOX

"""
Configuration Module
Contains configuration settings for the bot.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Blockchain configuration
BSC_RPC_URL = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
BSC_API_KEY = os.getenv("BSC_API_KEY")

# Wallet addresses
DEV_WALLET = os.getenv("DEV_WALLET")
MARKETING_WALLET = os.getenv("MARKETING_WALLET")
LIQUIDITY_WALLET = os.getenv("LIQUIDITY_WALLET")
PAYMENT_WALLET = os.getenv("PAYMENT_WALLET")

# Deployer private key
DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Pricing in BNB
UNLOCK_PRICE = 0.05
CMC_PRICE = 0.5
