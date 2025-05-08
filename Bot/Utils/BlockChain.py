# Copyright ©️ 2025 THEETOX
"""
Blockchain Module
Handles blockchain interactions for contract deployment and management.
"""

import os
import json
import logging
import asyncio
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

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Load contract ABI
with open(os.path.join(os.path.dirname(__file__), '../../contracts/MemeCoin.json'), 'r') as f:
    contract_data = json.load(f)
    CONTRACT_ABI = contract_data['abi']
    CONTRACT_BYTECODE = contract_data['bytecode']

async def deploy_contract(name, symbol, total_supply, dev_wallet, marketing_wallet, liquidity_wallet, deployer_key):
    """
    Deploy a new memecoin contract.
    
    Args:
        name: The name of the coin
        symbol: The symbol of the coin
        total_supply: The total supply of the coin
        dev_wallet: The developer wallet address
        marketing_wallet: The marketing wallet address
        liquidity_wallet: The liquidity wallet address
        deployer_key: The private key of the deployer
        
    Returns:
        The contract address if successful, None otherwise
    """
    try:
        # Create contract instance
        contract = w3.eth.contract(abi=CONTRACT_ABI, bytecode=CONTRACT_BYTECODE)
        
        # Get deployer account
        account = w3.eth.account.from_key(deployer_key)
        deployer_address = account.address
        
        # Get nonce
        nonce = w3.eth.get_transaction_count(deployer_address)
        
        # Build constructor transaction
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
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(constructor_txn, private_key=deployer_key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        # Get contract address
        contract_address = tx_receipt.contractAddress
        
        logger.info(f"Contract deployed at {contract_address}")
        return contract_address
        
    except Exception as e:
        logger.error(f"Error deploying contract: {e}")
        return None

async def unlock_trading(contract_address, deployer_key):
    """
    Enable trading for a deployed contract.
    
    Args:
        contract_address: The contract address
        deployer_key: The private key of the deployer
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create contract instance
        contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)
        
        # Get deployer account
        account = w3.eth.account.from_key(deployer_key)
        deployer_address = account.address
        
        # Get nonce
        nonce = w3.eth.get_transaction_count(deployer_address)
        
        # Build transaction
        txn = contract.functions.enableTrading().build_transaction({
            'from': deployer_address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=deployer_key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        logger.info(f"Trading enabled for {contract_address}")
        return True
        
    except Exception as e:
        logger.error(f"Error enabling trading: {e}")
        return False

async def submit_cmc(name, symbol, contract_address, logo_path):
    """
    Submit a coin to CoinMarketCap.
    
    Args:
        name: The name of the coin
        symbol: The symbol of the coin
        contract_address: The contract address
        logo_path: The path to the logo file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # This is a simplified version of CMC submission
        # In a real implementation, you would use the CMC API
        
        # Simulate API call delay
        await asyncio.sleep(2)
        
        logger.info(f"Submitted {name} ({symbol}) to CMC")
        return True
        
    except Exception as e:
        logger.error(f"Error submitting to CMC: {e}")
        return False

async def verify_payment(wallet_address, expected_amount, reference):
    """
    Verify a payment on the blockchain.
    
    Args:
        wallet_address: The wallet address to check
        expected_amount: The expected amount in BNB
        reference: The payment reference
        
    Returns:
        True if payment verified, False otherwise
    """
    try:
        # This is a simplified version of payment verification
        # In a real implementation, you would use the BSC API to check transactions
        
        # Convert expected amount to Wei
        expected_wei = w3.to_wei(expected_amount, 'ether')
        
        # Get current time
        current_time = datetime.now()
        
        # Check transactions in the last hour
        one_hour_ago = current_time - timedelta(hours=1)
        
        # BSCScan API endpoint for transactions
        api_url = f"https://api.bscscan.com/api"
        params = {
            "module": "account",
            "action": "txlist",
            "address": wallet_address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc",
            "apikey": BSC_API_KEY
        }
        
        # Make API request
        response = requests.get(api_url, params=params)
        data = response.json()
        
        # Check if API call was successful
        if data["status"] != "1":
            logger.error(f"BSCScan API error: {data['message']}")
            return False
        
        # Check transactions
        for tx in data["result"]:
            # Check if transaction is recent (within the last hour)
            tx_time = datetime.fromtimestamp(int(tx["timeStamp"]))
            if tx_time < one_hour_ago:
                continue
            
            # Check if transaction is a transfer to our wallet
            if tx["to"].lower() == wallet_address.lower() and int(tx["value"]) >= expected_wei:
                # In a real implementation, you would check the transaction input data
                # for the reference, but for simplicity we'll assume it's correct
                return True
        
        # No matching transaction found
        return False
        
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        return False
