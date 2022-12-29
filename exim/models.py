from decimal import Decimal


class Asset:
    def __init__(self, quantity: Decimal):
        assert quantity >= 0.0
        self._unlocked = quantity
        self._locked = Decimal("0.00")

    @property
    def unlocked(self) -> Decimal:
        return self._unlocked

    @property
    def locked(self) -> Decimal:
        return self._locked

    @unlocked.setter
    def unlocked(self, quantity: Decimal):
        assert quantity >= 0.0
        self._unlocked = quantity

    @locked.setter
    def locked(self, quantity: Decimal):
        assert quantity >= 0.0
        self._locked = quantity

    @property
    def total(self) -> Decimal:
        return self.locked + self.unlocked

    def __repr__(self) -> str:
        return f"Asset(total={self.total}, unlocked={self.unlocked}, locked={self.locked})"


class Account:
    def __init__(self, name: str):
        self.id = None
        self.name = name
        self.wallet = dict()
        self.orders = dict()

    def __repr__(self):
        return f"Account(id={self.id}, name={self.name})"


class Order:
    def __init__(self, time: int, owner: int, side: str, quantity: Decimal, price: Decimal = None):
        assert time >= 0
        assert quantity > 0.0
        assert price is None or price > 0.0
        self.id = None
        self.time = time
        self.owner = owner
        self.side = side
        self._quantity = quantity
        self.initial_quantity = quantity
        self.price = price
        self.status = None
        self.trades = []
        self.next = None
        self.prev = None

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        assert value >= 0.0
        self._quantity = value

    def __repr__(self):
        return f"Order(id={self.id}, side={self.side}, quantity={self.quantity}, price={self.price})"


class Trade:
    def __init__(self, time: int, side: str, quantity: Decimal, price: Decimal, maker: int, taker: int):
        assert quantity > 0.0
        assert price > 0.0
        self.id = None
        self.time = time
        self.side = side
        self.quantity = quantity
        self.price = price
        self.maker = maker
        self.taker = taker

    def __repr__(self):
        return f"Trade(id={self.id}, time={self.time}, side={self.side}, quantity={self.quantity},  price={self.price})"
