from .orderbook import OrderBook
from .models import Order, Trade
import itertools
import time


class Market:
    def __init__(self, base: str, qoute: str):
        self.base = base
        self.qoute = qoute
        self.symbol = f"{self.base}{self.qoute}"
        self.orderbook = OrderBook()
        self.orders = dict()
        self.trades = dict()
        self.trades_history = []
        self.order_id_counter = itertools.count()
        self.trade_id_counter = itertools.count()

    @property
    def best_bid(self):
        return self.orderbook.bids.top.price if self.orderbook.bids.top else None

    @property
    def best_ask(self):
        return self.orderbook.asks.top.price if self.orderbook.asks.top else None

    @property
    def last_price(self):
        return self.trades_history[-1]["price"] if self.trades else None

    @property
    def mid_price(self):
        return (self.best_bid + self.best_ask) / 2 if self.best_bid and self.best_ask else None

    def process_order(self, order: Order):
        def trade(maker: Order, taker: Order):
            # trades maker and taker orders against each other
            amount = min(maker.quantity, taker.quantity)
            maker.quantity -= amount
            taker.quantity -= amount
            _trade = Trade(
                time=time.time_ns(),
                side=maker.side,
                quantity=amount,
                price=maker.price,
                maker=maker.owner,
                taker=taker.owner,
            )
            _trade.id = next(self.trade_id_counter)
            self.trades[_trade.id] = _trade
            self.trades_history.append(
                dict(time=_trade.time, price=float(_trade.price), quantity=float(_trade.quantity))
            )
            trades.append(_trade.id)
            maker.trades.append(_trade.id)
            taker.trades.append(_trade.id)
            return amount

        def _recursive_process(order: Order):
            # recursively trades orders against each other
            if order.side == "BUY":
                if order.price is not None:  # process limit order
                    maker = self.orderbook.asks.top
                    if not maker or order.price < maker.price:
                        self.orderbook.bids.push(order)
                        return
                    else:
                        amount = trade(maker, order)
                        self.orderbook.asks.depth[maker.price] -= amount
                        self.orderbook.asks.volume -= amount
                        if maker.quantity == 0:
                            self.orderbook.asks.pop(maker)
                            self.orders[maker.id].status = "FILLED"
                            filled_orders.append(maker.id)
                        if order.quantity > 0:
                            _recursive_process(order)
                        else:
                            self.orders[order.id].status = "FILLED"
                            filled_orders.append(order.id)
                            return
                else:  # process market order
                    maker = self.orderbook.asks.top
                    amount = trade(maker, order)
                    self.orderbook.asks.depth[maker.price] -= amount
                    self.orderbook.asks.volume -= amount
                    if maker.quantity == 0:
                        self.orderbook.asks.pop(maker)
                        self.orders[maker.id].status = "FILLED"
                        filled_orders.append(maker.id)
                    if order.quantity > 0:
                        _recursive_process(order)
                    else:
                        self.orders[order.id].status = "FILLED"
                        filled_orders.append(order.id)
                        return

            if order.side == "SELL":
                if order.price is not None:  # process limit order
                    maker = self.orderbook.bids.top
                    if not maker or order.price > maker.price:
                        self.orderbook.asks.push(order)
                        return
                    else:
                        amount = trade(maker, order)
                        self.orderbook.bids.depth[maker.price] -= amount
                        self.orderbook.bids.volume -= amount
                        if maker.quantity == 0:
                            self.orderbook.bids.pop(maker)
                            self.orders[maker.id].status = "FILLED"
                            filled_orders.append(maker.id)
                        if order.quantity > 0:
                            _recursive_process(order)
                        else:
                            self.orders[order.id].status = "FILLED"
                            filled_orders.append(order.id)
                            return
                else:  # process market order
                    maker = self.orderbook.bids.top
                    amount = trade(maker, order)
                    self.orderbook.bids.depth[maker.price] -= amount
                    self.orderbook.bids.volume -= amount
                    if maker.quantity == 0:
                        self.orderbook.bids.pop(maker)
                        self.orders[maker.id].status = "FILLED"
                        filled_orders.append(maker.id)
                    if order.quantity > 0:
                        _recursive_process(order)
                    else:
                        self.orders[order.id].status = "FILLED"
                        filled_orders.append(order.id)
                        return

        trades = []
        filled_orders = []
        _recursive_process(order)
        return trades, filled_orders
