# Copyright ©️ 2025THE ETOX
# Memecoin Generator Bot Deployment Script
# This script sets up the environment and deploys the bot

echo "Setting up Memecoin Generator Bot..."

# Create necessary directories
mkdir -p logs
mkdir -p database
mkdir -p logos

# Install dependencies
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Bot Configuration
TELEGRAM_TOKEN=your_telegram_token_here

# Blockchain Configuration
BSC_RPC_URL=https://bsc-dataseed.binance.org/
BSC_API_KEY=your_bscscan_api_key_here

# Wallet Addresses
DEV_WALLET=your_dev_wallet_address_here
MARKETING_WALLET=your_marketing_wallet_address_here
LIQUIDITY_WALLET=your_liquidity_wallet_address_here
PAYMENT_WALLET=your_payment_wallet_address_here

# Deployer Private Key (Keep this secure!)
DEPLOYER_PRIVATE_KEY=your_deployer_private_key_here

# OpenAI API Key (for shill message generation)
OPENAI_API_KEY=your_openai_api_key_here
EOL
    echo "Please edit the .env file with your actual configuration values."
fi

# Compile the smart contract
echo "Compiling smart contract..."
# This is a placeholder - in a real deployment, you would use truffle or hardhat
# npx truffle compile

# Initialize the database
echo "Initializing database..."
python -c "from bot.utils.database import setup_database; setup_database()"

# Start the bot
echo "Starting the bot..."
python -m bot.bot

echo "Deployment complete!"

