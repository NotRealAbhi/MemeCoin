# Copyright ©️ 2025 THEETOX
"""
Blockchain Module
Handles blockchain interactions for contract deployment and management.
"""

import os
import json
import logging
import asyncio
import traceback
from web3 import Web3
from web3.middleware import geth_poa_middleware
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
BSC_RPC_URL = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
BSC_API_KEY = os.getenv("BSC_API_KEY")
DEV_WALLET = os.getenv("DEV_WALLET")
MARKETING_WALLET = os.getenv("MARKETING_WALLET")
LIQUIDITY_WALLET = os.getenv("LIQUIDITY_WALLET")
PAYMENT_WALLET = os.getenv("PAYMENT_WALLET")

if not BSC_API_KEY:
    logger.warning("BSC_API_KEY not set. BSCScan features may not work.")

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Load contract ABI and bytecode safely
try:
    contract_json_path = os.path.join(os.path.dirname(__file__), '../../Bot/Contracts/MemeCoin.json')
    with open(contract_json_path, 'r') as f:
        contract_data = json.load(f)
        CONTRACT_ABI = contract_data['abi']
        CONTRACT_BYTECODE = contract_data['bytecode']
except FileNotFoundError:
    logger.error("MemeCoin.json not found. Please check the path.")
    CONTRACT_ABI = None
    CONTRACT_BYTECODE = None
except json.JSONDecodeError as e:
    logger.error(f"Failed to decode MemeCoin.json: {e}")
    CONTRACT_ABI = None
    CONTRACT_BYTECODE = None


async def deploy_contract(name, symbol, total_supply, dev_wallet, marketing_wallet, liquidity_wallet, deployer_key):
    """
    Deploy a new memecoin contract.
    """
    try:
        if CONTRACT_ABI is None or CONTRACT_BYTECODE is None:
            raise RuntimeError("Contract ABI or Bytecode not loaded properly.")

        contract = w3.eth.contract(abi=CONTRACT_ABI, bytecode=CONTRACT_BYTECODE)
        account = w3.eth.account.from_key(deployer_key)
        deployer_address = account.address
        nonce = w3.eth.get_transaction_count(deployer_address)
        gas_price = w3.eth.gas_price or w3.to_wei("5", "gwei")

        constructor_txn = contract.constructor(
            name,
            symbol,
            total_supply,
            dev_wallet,
            marketing_wallet,
            liquidity_wallet
        ).build_transaction({
            'from': deployer_address,
            'nonce': nonce,
            'gas': 5000000,
            'gasPrice': gas_price
        })

        signed_txn = w3.eth.account.sign_transaction(constructor_txn, private_key=deployer_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        contract_address = tx_receipt.contractAddress

        logger.info(f"Contract deployed at {contract_address}")
        return contract_address

    except Exception:
        logger.error("Error deploying contract:\n%s", traceback.format_exc())
        return None


async def unlock_trading(contract_address, deployer_key):
    """
    Enable trading for a deployed contract.
    """
    try:
        if CONTRACT_ABI is None:
            raise RuntimeError("Contract ABI not loaded.")

        contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)
        account = w3.eth.account.from_key(deployer_key)
        deployer_address = account.address
        nonce = w3.eth.get_transaction_count(deployer_address)
        gas_price = w3.eth.gas_price or w3.to_wei("5", "gwei")

        txn = contract.functions.enableTrading().build_transaction({
            'from': deployer_address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': gas_price
        })

        signed_txn = w3.eth.account.sign_transaction(txn, private_key=deployer_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        logger.info(f"Trading enabled for {contract_address}")
        return True

    except Exception:
        logger.error("Error enabling trading:\n%s", traceback.format_exc())
        return False


async def submit_cmc(name, symbol, contract_address, logo_path):
    """
    Submit a coin to CoinMarketCap (mocked version).
    """
    try:
        await asyncio.sleep(2)  # Simulate delay
        logger.info(f"Submitted {name} ({symbol}) to CMC")
        return True

    except Exception:
        logger.error("Error submitting to CMC:\n%s", traceback.format_exc())
        return False


async def verify_payment(wallet_address, expected_amount, reference):
    """
    Verify a payment on the blockchain.
    """
    try:
        expected_wei = w3.to_wei(expected_amount, 'ether')
        current_time = datetime.now()
        one_hour_ago = current_time - timedelta(hours=1)

        api_url = "https://api.bscscan.com/api"
        params = {
            "module": "account",
            "action": "txlist",
            "address": wallet_address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc",
            "apikey": BSC_API_KEY
        }

        response = requests.get(api_url, params=params)
        data = response.json()

        if data.get("status") != "1":
            logger.error(f"BSCScan API error: {data.get('message')}")
            return False

        for tx in data["result"]:
            tx_time = datetime.fromtimestamp(int(tx["timeStamp"]))
            if tx_time < one_hour_ago:
                continue

            if tx["to"].lower() == wallet_address.lower() and int(tx["value"]) >= expected_wei:
                return True

        return False

    except Exception:
        logger.error("Error verifying payment:\n%s", traceback.format_exc())
        return False
        
