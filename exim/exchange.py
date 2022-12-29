from .models import Asset, Account, Order
from .market import Market
from decimal import Decimal
import pandas as pd
import itertools
import time


class Exchange:
    def __init__(self, verbose=True):
        self.symbols = []
        self.unit_decimals = dict()
        self.markets = dict()
        self.accounts = dict()
        self.account_id_counter = itertools.count()
        self.verbose = verbose

    def register_symbol(self, symbol: str, unit_decimals: int = 0):
        symbol = symbol.upper()
        self.symbols.append(symbol)
        self.unit_decimals[symbol] = unit_decimals
        if self.verbose:
            print(f"Symbol registered: {symbol}")
        return True

    def register_market(self, base: str, qoute: str):
        base = base.upper()
        qoute = qoute.upper()
        if base in self.symbols and qoute in self.symbols:
            market = Market(base, qoute)
            self.markets[market.symbol] = market
            if self.verbose:
                print(f"Market registered: {market.symbol}")
            return True
        if self.verbose:
            print("Register failed: symbol not listed")
        return False

    def register_account(self, name: str):
        account = Account(name=name)
        account.id = next(self.account_id_counter)
        for symbol in self.symbols:
            account.wallet[symbol] = Asset(Decimal("0.0"))
        for symbol in self.markets.keys():
            account.orders[symbol] = dict(open=[], closed=[])
        self.accounts[account.id] = account
        if self.verbose:
            print(f"Account registered with id: {account.id}")
        return True

    def deposit(self, account_id: int, symbol: str, quantity: float):
        symbol = symbol.upper()
        quantity = Decimal(str(round(quantity, self.unit_decimals[symbol])))
        self.accounts[account_id].wallet[symbol].unlocked += quantity
        if self.verbose:
            print("Deposit successful")
        return True

    def withdraw(self, account_id: int, symbol: str, quantity: float):
        symbol = symbol.upper()
        quantity = Decimal(str(round(quantity, self.unit_decimals[symbol])))
        if 0 < quantity <= self.accounts[account_id].wallet[symbol].unlocked:
            self.accounts[account_id].wallet[symbol].unlocked += quantity
            if self.verbose:
                print("Withdraw successful")
            return True
        if self.verbose:
            print("Withdraw failed")
        return False

    def buy(self, account_id: int, market: str, quantity: Decimal, price: Decimal = None):
        def _calculate_buy_cost(market: str, quantity: Decimal, price: Decimal):
            # calculate buy cost according to existing ask orders
            cost = 0
            quantity_to_trade = quantity
            depth = self.markets[market].orderbook.asks.depth.copy()
            if price is not None:
                while depth:
                    ask_price, ask_volume = depth.popitem(0)
                    if price <= ask_price:
                        cost += quantity_to_trade * price
                        return cost
                    else:
                        if quantity_to_trade <= ask_volume:
                            cost += quantity_to_trade * ask_price
                            quantity_to_trade = 0
                            return cost
                        else:
                            cost += ask_volume * ask_price
                            quantity_to_trade -= ask_volume
                cost += quantity_to_trade * price
                quantity_to_trade = 0
                return cost
            else:
                while depth:
                    ask_price, ask_volume = depth.popitem(0)
                    if quantity_to_trade <= ask_volume:
                        cost += quantity_to_trade * ask_price
                        quantity_to_trade = 0
                        return cost
                    else:
                        cost += ask_volume * ask_price
                        quantity_to_trade -= ask_volume
                if quantity_to_trade:
                    return None
                return cost

        # fetch market and account
        if account_id not in self.accounts.keys():
            if self.verbose:
                print("Failed: invalid account id")
            return False
        if market not in self.markets.keys():
            if self.verbose:
                print("Failed: invalid market")
            return False
        market = self.markets[market.upper()]
        account = self.accounts[account_id]
        # convert to decimal
        quantity = Decimal(str(round(quantity, self.unit_decimals[market.base])))
        price = Decimal(str(round(price, self.unit_decimals[market.qoute]))) if price else None
        if quantity <= 0:
            if self.verbose:
                print("Failed: invalid quantity")
            return False
        if price is not None and price <= 0:
            if self.verbose:
                print("Failed: invalid price")
            return False
        # detemine cost
        cost = _calculate_buy_cost(market.symbol, quantity, price)
        # validate
        if cost is None:
            # not enough orders to trade
            if self.verbose:
                print("Failed: not enough orders to trade")
            return False
        if account.wallet[market.qoute].unlocked < cost:
            if self.verbose:
                print("Failed: not enough balance")
            return False
        # lock balance
        account.wallet[market.qoute].unlocked -= cost
        account.wallet[market.qoute].locked += cost
        # create order
        order = Order(
            time=time.time_ns(),
            owner=account.id,
            side="BUY",
            quantity=quantity,
            price=price,
        )
        # register order
        order.id = next(market.order_id_counter)
        order.status = "OPEN"
        market.orders[order.id] = order
        account.orders[market.symbol]["open"].append(order.id)
        # process order
        trades, filled_orders = market.process_order(order=order)
        # review trades and apply transactions
        for tid in trades:
            # fetch trade
            trade = market.trades[tid]
            # fetch maker and taker and adjust assets
            maker = self.accounts[trade.maker]  # seller
            taker = self.accounts[trade.taker]  # buyer
            maker.wallet[market.base].locked -= trade.quantity
            maker.wallet[market.qoute].unlocked += trade.quantity * trade.price
            taker.wallet[market.qoute].locked -= trade.quantity * trade.price
            taker.wallet[market.base].unlocked += trade.quantity
        # handle account orders
        for order_id in filled_orders:
            owner = self.accounts[market.orders[order_id].owner]
            owner.orders[market.symbol]["open"].remove(order_id)
            owner.orders[market.symbol]["closed"].append(order_id)
        if self.verbose:
            print(f"Order executed with id: {order.id}")
        return True

    def sell(self, account_id: int, market: str, quantity: Decimal, price: Decimal = None):
        # fetch market and account
        if account_id not in self.accounts.keys():
            if self.verbose:
                print("Failed: invalid account id")
            return False
        if market not in self.markets.keys():
            if self.verbose:
                print("Failed: invalid market")
            return False
        market = self.markets[market.upper()]
        account = self.accounts[account_id]
        # convert to decimal
        quantity = Decimal(str(round(quantity, self.unit_decimals[market.base])))
        price = Decimal(str(round(price, self.unit_decimals[market.qoute]))) if price else None
        if quantity <= 0:
            if self.verbose:
                print("Failed: invalid quantity")
            return False
        if price is not None and price <= 0:
            if self.verbose:
                print("Failed: invalid price")
            return False
        # detemine cost
        cost = quantity
        # validate
        if price is None and cost > market.orderbook.bids.volume:
            # not enough orders to trade
            if self.verbose:
                print("Failed: not enough orders to trade")
            return False
        if account.wallet[market.base].unlocked < cost:
            if self.verbose:
                print("Failed: not enough balance")
            return False
        # lock shares
        account.wallet[market.base].unlocked -= cost
        account.wallet[market.base].locked += cost
        # create order
        order = Order(
            time=time.time_ns(),
            owner=account.id,
            side="SELL",
            quantity=quantity,
            price=price,
        )
        # register order
        order.id = next(market.order_id_counter)
        order.status = "OPEN"
        market.orders[order.id] = order
        account.orders[market.symbol]["open"].append(order.id)
        # process order
        trades, filled_orders = market.process_order(order=order)
        # review trades and apply transactions
        for tid in trades:
            # fetch trade
            trade = market.trades[tid]
            # fetch maker and taker and adjust assets
            maker = self.accounts[trade.maker]  # buyer
            taker = self.accounts[trade.taker]  # seller
            maker.wallet[market.qoute].locked -= trade.quantity * trade.price
            maker.wallet[market.base].unlocked += trade.quantity
            taker.wallet[market.base].locked -= trade.quantity
            taker.wallet[market.qoute].unlocked += trade.quantity * trade.price
        # handle account orders
        for order_id in filled_orders:
            owner = self.accounts[market.orders[order_id].owner]
            owner.orders[market.symbol]["open"].remove(order_id)
            owner.orders[market.symbol]["closed"].append(order_id)
        if self.verbose:
            print(f"Order executed with id: {order.id}")
        return True

    def cancel(self, account_id: int, market: str, order_id: int):
        if account_id not in self.accounts.keys():
            if self.verbose:
                print("Failed: invalid account id")
            return False
        if market not in self.markets.keys():
            if self.verbose:
                print("Failed: invalid market")
            return False
        # fetch market and account
        market = self.markets[market.upper()]
        account = self.accounts[account_id]
        # fetch order
        order = market.orders.get(order_id, None)
        # validate
        if order and order.owner == account_id and order.status == "OPEN":
            # pop order from orderbook and return values
            if order.side == "BUY":
                market.orderbook.bids.pop(order)
                market.orders[order.id].status = "CANCELED"
                account.wallet[market.qoute].locked -= order.quantity * order.price
                account.wallet[market.qoute].unlocked += order.quantity * order.price
                account.orders[market.symbol]["open"].remove(order.id)
                account.orders[market.symbol]["closed"].append(order.id)
                if self.verbose:
                    print(f"Order canceled with id: {order.id}")
                return True
            if order.side == "SELL":
                market.orderbook.asks.pop(order)
                market.orders[order.id].status = "CANCELED"
                account.wallet[market.base].locked -= order.quantity
                account.wallet[market.base].unlocked += order.quantity
                account.orders[market.symbol]["open"].remove(order.id)
                account.orders[market.symbol]["closed"].append(order.id)
                if self.verbose:
                    print(f"Order canceled with id: {order.id}")
                return True
        if self.verbose:
            print("Failed: order not found")
        return False

    def process_order_qoute(self, qoute: dict):
        if qoute.get("order_id"):
            self.cancel(qoute["account_id"], qoute["market"], qoute["order_id"])
        else:
            if qoute["side"].upper() == "BUY":
                self.buy(qoute["account_id"], qoute["market"], qoute["quantity"], qoute.get("price"))
            if qoute["side"].upper() == "SELL":
                self.sell(qoute["account_id"], qoute["market"], qoute["quantity"], qoute.get("price"))

    def get_trades(self, market: str):
        if market not in self.markets.keys():
            if self.verbose:
                print("Failed: invalid market")
            return None
        trades = self.markets[market.upper()].trades_history
        trades = pd.DataFrame(trades, columns=["time", "price", "quantity"])
        return trades

    def get_orderbook(self, market: str):
        if market not in self.markets.keys():
            if self.verbose:
                print("Failed: invalid market")
            return None
        bids = list(self.markets[market.upper()].orderbook.bids.depth.items())
        asks = list(self.markets[market.upper()].orderbook.asks.depth.items())
        bids = pd.DataFrame(bids, columns=["price", "volume"])
        asks = pd.DataFrame(asks, columns=["price", "volume"])
        bids["type"] = "BID"
        asks["type"] = "ASK"
        orderbook = bids.append(asks).sort_values("price")
        orderbook.set_index("price", inplace=True)
        return orderbook

    def get_orders(self, account_id: int, market: str, status: str = None):
        if account_id not in self.accounts.keys():
            if self.verbose:
                print("Failed: invalid account id")
            return None
        if market not in self.markets.keys():
            if self.verbose:
                print("Failed: invalid market")
            return None
        open_order_ids = self.accounts[account_id].orders[market.upper()]["open"]
        closed_order_ids = self.accounts[account_id].orders[market.upper()]["closed"]
        orders = []
        for id in open_order_ids + closed_order_ids:
            order = self.markets[market.upper()].orders[id]
            orders.append((order.id, order.time, order.side, order.initial_quantity, order.price, order.status))
        orders = pd.DataFrame(orders, columns=["id", "time", "side", "quantity", "price", "status"])
        orders.insert(2, "type", orders.price.map(lambda x: "MARKET" if x is None else "LIMIT"))
        orders.sort_values(["id"], ascending=False, inplace=True)
        orders.set_index("id", inplace=True)
        if status:
            return orders.loc[orders.status == status.upper()]
        return orders

    def get_wallet(self, account_id: str):
        if account_id not in self.accounts.keys():
            if self.verbose:
                print("Failed: invalid account id")
            return None
        account = self.accounts[account_id]
        assets = []
        for symbol in account.wallet.keys():
            assets.append(
                (
                    symbol,
                    account.wallet[symbol].total,
                    account.wallet[symbol].unlocked,
                )
            )
        wallet = pd.DataFrame(assets, columns=["symbol", "total", "available"])
        wallet.set_index("symbol", inplace=True)
        return wallet

    def get_accounts(self):
        accounts = pd.DataFrame(columns=["Name"] + self.symbols, index=list(self.accounts.keys()))
        for account in self.accounts.values():
            wallet = self.get_wallet(account_id=account.id)
            assets = [account.name] + list(wallet["total"].values)
            accounts.loc[account.id] = assets
        accounts.index.rename("id", inplace=True)
        return accounts
