# Copyright ©️ 2025 @THEETOX

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

interface IUniswapV2Factory {
    function createPair(address tokenA, address tokenB) external returns (address pair);
}

interface IUniswapV2Router02 {
    function factory() external pure returns (address);
    function WETH() external pure returns (address);
    function swapExactTokensForETHSupportingFeeOnTransferTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external;
    function addLiquidityETH(
        address token,
        uint amountTokenDesired,
        uint amountTokenMin,
        uint amountETHMin,
        address to,
        uint deadline
    ) external payable returns (uint amountToken, uint amountETH, uint liquidity);
}

contract MemeCoin is ERC20, Ownable {
    using SafeMath for uint256;
    
    // Token parameters
    uint256 public buyTax = 5;
    uint256 public sellTax = 7;
    uint256 public devFee = 2;
    
    // Trading status
    bool public tradingEnabled = false;
    
    // Addresses
    address public devWallet;
    address public marketingWallet;
    address public liquidityWallet;
    
    // Uniswap interfaces
    IUniswapV2Router02 public uniswapV2Router;
    address public uniswapV2Pair;
    
    // Exclusions from fees
    mapping(address => bool) private _isExcludedFromFees;
    
    // Events
    event TradingEnabled(bool enabled);
    event ExcludeFromFees(address indexed account, bool excluded);
    event TaxUpdated(uint256 buyTax, uint256 sellTax, uint256 devFee);
    event WalletsUpdated(address devWallet, address marketingWallet, address liquidityWallet);
    event SwapAndLiquify(uint256 tokensSwapped, uint256 ethReceived, uint256 tokensIntoLiquidity);
    
    constructor(
        string memory name_,
        string memory symbol_,
        uint256 totalSupply_,
        address devWallet_,
        address marketingWallet_,
        address liquidityWallet_
    ) ERC20(name_, symbol_) {
        devWallet = devWallet_;
        marketingWallet = marketingWallet_;
        liquidityWallet = liquidityWallet_;
        
        // Create total supply
        _mint(msg.sender, totalSupply_ * 10**decimals());
        
        // Set up Uniswap router (PancakeSwap for BSC)
        IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(0x10ED43C718714eb63d5aA57B78B54704E256024E); // PancakeSwap Router v2
        uniswapV2Pair = IUniswapV2Factory(_uniswapV2Router.factory())
            .createPair(address(this), _uniswapV2Router.WETH());
        uniswapV2Router = _uniswapV2Router;
        
        // Exclude special addresses from fees
        _isExcludedFromFees[owner()] = true;
        _isExcludedFromFees[address(this)] = true;
        _isExcludedFromFees[devWallet] = true;
        _isExcludedFromFees[marketingWallet] = true;
        _isExcludedFromFees[liquidityWallet] = true;
    }
    
    // Enable trading (can only be called by owner)
    function enableTrading() external onlyOwner {
        require(!tradingEnabled, "Trading is already enabled");
        tradingEnabled = true;
        emit TradingEnabled(true);
    }
    
    // Update tax rates (can only be called by owner)
    function updateTaxes(uint256 _buyTax, uint256 _sellTax, uint256 _devFee) external onlyOwner {
        require(_buyTax <= 10, "Buy tax cannot exceed 10%");
        require(_sellTax <= 15, "Sell tax cannot exceed 15%");
        require(_devFee <= 5, "Dev fee cannot exceed 5%");
        
        buyTax = _buyTax;
        sellTax = _sellTax;
        devFee = _devFee;
        
        emit TaxUpdated(buyTax, sellTax, devFee);
    }
    
    // Update wallet addresses (can only be called by owner)
    function updateWallets(
        address _devWallet,
        address _marketingWallet,
        address _liquidityWallet
    ) external onlyOwner {
        require(_devWallet != address(0), "Dev wallet cannot be zero address");
        require(_marketingWallet != address(0), "Marketing wallet cannot be zero address");
        require(_liquidityWallet != address(0), "Liquidity wallet cannot be zero address");
        
        devWallet = _devWallet;
        marketingWallet = _marketingWallet;
        liquidityWallet = _liquidityWallet;
        
        _isExcludedFromFees[_devWallet] = true;
        _isExcludedFromFees[_marketingWallet] = true;
        _isExcludedFromFees[_liquidityWallet] = true;
        
        emit WalletsUpdated(_devWallet, _marketingWallet, _liquidityWallet);
    }
    
    // Exclude/include address from fees
    function excludeFromFees(address account, bool excluded) external onlyOwner {
        _isExcludedFromFees[account] = excluded;
        emit ExcludeFromFees(account, excluded);
    }
    
    // Check if address is excluded from fees
    function isExcludedFromFees(address account) public view returns (bool) {
        return _isExcludedFromFees[account];
    }
    
    // Override transfer function to apply taxes
    function _transfer(
        address from,
        address to,
        uint256 amount
    ) internal override {
        require(from != address(0), "ERC20: transfer from the zero address");
        require(to != address(0), "ERC20: transfer to the zero address");
        
        // Check if trading is enabled
        if (!tradingEnabled && 
            from != owner() && 
            to != owner() && 
            from != address(this) &&
            !_isExcludedFromFees[from] && 
            !_isExcludedFromFees[to]) {
            revert("Trading is not enabled yet");
        }
        
        // No fees for excluded addresses
        if (_isExcludedFromFees[from] || _isExcludedFromFees[to]) {
            super._transfer(from, to, amount);
            return;
        }
        
        // Calculate and apply taxes
        uint256 taxAmount = 0;
        
        // Buy transaction (from pair to user)
        if (from == uniswapV2Pair && to != address(uniswapV2Router)) {
            taxAmount = amount.mul(buyTax).div(100);
        }
        // Sell transaction (from user to pair)
        else if (to == uniswapV2Pair && from != address(uniswapV2Router)) {
            taxAmount = amount.mul(sellTax).div(100);
        }
        
        // If there are taxes to apply
        if (taxAmount > 0) {
            // Calculate distribution
            uint256 devAmount = taxAmount.mul(devFee).div(buyTax > sellTax ? buyTax : sellTax);
            uint256 remainingTax = taxAmount.sub(devAmount);
            uint256 marketingAmount = remainingTax.div(2);
            uint256 liquidityAmount = remainingTax.sub(marketingAmount);
            
            // Transfer taxes
            super._transfer(from, devWallet, devAmount);
            super._transfer(from, marketingWallet, marketingAmount);
            super._transfer(from, liquidityWallet, liquidityAmount);
            
            // Transfer remaining amount to recipient
            super._transfer(from, to, amount.sub(taxAmount));
        } else {
            // No taxes, transfer full amount
            super._transfer(from, to, amount);
        }
    }
    
    // Function to add liquidity (50% tokens + 0.5 BNB)
    function addLiquidity(uint256 tokenAmount) external payable onlyOwner {
        require(msg.value >= 0.5 ether, "Must provide at least 0.5 BNB");
        
        // Approve token transfer to cover all possible scenarios
        _approve(address(this), address(uniswapV2Router), tokenAmount);
        
        // Add the liquidity
        uniswapV2Router.addLiquidityETH{
            value: msg.value
        }(
            address(this),
            tokenAmount,
            0, // slippage is unavoidable
            0, // slippage is unavoidable
            owner(),
            block.timestamp
        );
    }
    
    // Function to receive ETH when swapping
    receive() external payable {}
}

