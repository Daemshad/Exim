# Exim

Exim is a stock market exchange simulator with fast limit orderbook and account management system for analyzing the interactions between multiple market participants.

## Installation

install using setup.py

## Usage
  import
```python
from  exim  import  Exchange
```
define an exchange
```python
e  =  Exchange(verbose=Ture)
```
define symbols
```python
e.register_symbol("usd", unit_decimals=2)
e.register_symbol("btc", unit_decimals=8)
```
```
>> Symbol registered: USD
>> Symbol registered: BTC
```
define markets
```python
e.register_market(base="btc", qoute="usd")
```
```
>> Market registered: BTCUSD
```
register accounts
```python
e.register_account(name="Bob")
e.register_account(name="Alice")
```
```
>> Account registered with id: 0
>> Account registered with id: 1
```
deposit
```python
e.deposit(account_id=0, symbol="usd", quantity=1000000)
e.deposit(account_id=0, symbol="btc", quantity=1000)
e.deposit(account_id=1, symbol="usd", quantity=1000000)
e.deposit(account_id=1, symbol="btc", quantity=1000)
```
```
>> Deposit successful 
>> Deposit successful 
>> Deposit successful 
>> Deposit successful
```
process order qoute
```python
qoute  = {
	'account_id': 0,
	'market': 'BTCUSD',
	'side': 'BUY',
	'quantity': 0.2,
	'price': 16200.5
}
e.process_order_qoute(qoute)
```
```
>> Order executed with id: 0
```
cancel order
```python
e.cancel(account_id=0, market="BTCUSD", order_id=0)
```
```
>> Order canceled with id: 0
```
get trades history
```python
e.get_trades(market="BTCUSD")
```
```
                      time     price  quantity
0      1672302604364030000  16200.33  0.565952
1      1672302604364075000  16203.32  1.546563
2      1672302604364924000  16193.15  0.755235
3      1672302604365291000  16199.36  0.410144
4      1672302604366264000  16203.32  1.848169
...                    ...       ...       ...
11133  1672302611115437000  16198.83  0.006074
11134  1672302611207469000  16198.83  0.003008
11135  1672302611207509000  16199.26  0.000425
11136  1672302611604003000  16198.78  0.002434
11137  1672302611932396000  16198.78  0.000141
```
get orderbook
```python
e.get_orderbook(market="BTCUSD")
```
```
              volume type
price                    
16164.59  1.88399693  BID
16166.99  2.70263001  BID
16168.14  2.36591089  BID
16169.4   0.08754484  BID
16169.76   2.2795814  BID
...              ...  ...
16232.83  1.89113624  ASK
16233.64  3.61171658  ASK
16235.85  0.90120531  ASK
16235.89  0.76124634  ASK
16239.0   3.80998147  ASK
```
get all orders
```python
e.get_orders(account_id=0, market="BTCUSD")
```
```
                      time    type  side    quantity     price  status
id                                                                    
12045  1672302611971303000   LIMIT  SELL  0.00176843  16204.59    OPEN
12044  1672302611932366000  MARKET  SELL  0.00014146      None  FILLED
12042  1672302611684556000   LIMIT  SELL  0.00498656   16204.0    OPEN
12041  1672302611603964000   LIMIT  SELL  0.00243352  16185.77  FILLED
12039  1672302611207445000  MARKET   BUY  0.00343239      None  FILLED
...                    ...     ...   ...         ...       ...     ...
8      1672302604365465000   LIMIT   BUY  0.49533014  16198.55  FILLED
5      1672302604364908000   LIMIT   BUY  3.06846741  16199.36  FILLED
4      1672302604364720000   LIMIT   BUY  2.84544539  16192.97  FILLED
3      1672302604364537000   LIMIT  SELL  0.75523509  16193.15  FILLED
0      1672302604363567000   LIMIT  SELL  3.39473274  16203.32  FILLED
```
get accounts
```python
e.get_accounts()
```
```
     Name                 USD            BTC
id                                          
0     Bob   735756.2878483156  1016.14315807
1   Alice  1264243.7121516844   983.85684193
```
get wallet info
```python
e.get_wallet(account_id=0)
```
```
                    total       available
symbol                                   
USD     735756.2878483156  205.3250532967
BTC         1016.14315807      0.00227921
```
