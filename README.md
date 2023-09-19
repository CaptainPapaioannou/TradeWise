# TradeWise
##Web app via which you can manage virtual portfolios of stocks.

## Features
 -"Buy" and "Sell" real stocks in real time with the use of Yahoo Finance API
 -Play around in the stock market and learn how to trade without risking your real money
 -Manage multiple portfolios and interact with different accounts


## Installation
-Download the files
-Install Flask (if you haven't allready)
-On your bash command prompt, cd into the directory of the downloaded files
-Execute:
```
flask run
```


## Usage
1. Start by clicking on the "Register" button to create an account.
2. Complete the registration form. Please ensure you remember your password, as there is no option for resetting a forgotten password.
3. Once you've successfully logged in, you can perform the following actions:
  - Click on the "Quote" feature to check the current stock prices for most available stocks.
  - Click on the "Buy" option to purchase stocks by specifying the stock name and the desired quantity of shares.
  - Click on the "Sell" option to sell stocks by selecting the stock you wish to sell and specifying the quantity of shares.
  - Click on "History" to browse all transactions from that particular user account

## Limitations
- There's no stock browsing at the momment. You need to specify the exact stock symbol (usally 3-4 letters) to find the company you are looking for
- If you forget your password you can't access your account
- Styling is really limited at the momment

## Future Enhancements
- Improved UI/UX design
- Dark mode option
- Profile section with addition account settings

## Acknowledgments
- Special thanks to CS50, IEX cloud, Yahoo finance
