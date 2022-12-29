from .models import Order
from sortedcontainers import SortedDict


class OrderQueue:
    def __init__(self):
        self.head = None
        self.tail = None

    def empty(self):
        return self.head is None

    def append(self, order: Order):
        if self.empty():
            self.head = order
            self.tail = self.head
        else:
            self.tail.next = order
            self.tail.next.prev = self.tail
            self.tail = self.tail.next
        return

    def remove(self, order: Order):
        if self.head == self.tail:
            self.head = None
            self.tail = None
        elif order == self.head:
            self.head = self.head.next
            self.head.prev = None
        elif order == self.tail:
            self.tail = self.tail.prev
            self.tail.next = None
        else:
            order.prev.next = order.next
            order.next.prev = order.prev
        order.next = None
        order.prev = None
        return True


class OrderTree:
    def __init__(self, ascending=False):
        self.ascending = ascending
        self.tree = SortedDict()
        self.depth = SortedDict()
        self.volume = 0

    def push(self, order: Order):
        if self.tree.get(order.price) is None:
            self.tree[order.price] = OrderQueue()
            self.depth[order.price] = 0
        self.tree[order.price].append(order)
        self.depth[order.price] += order.quantity
        self.volume += order.quantity

    def pop(self, order: Order):
        self.tree[order.price].remove(order)
        self.depth[order.price] -= order.quantity
        self.volume -= order.quantity
        if self.tree[order.price].empty():
            self.tree.pop(order.price)
            self.depth.pop(order.price)

    @property
    def top(self):
        if not self.tree:
            return None
        if self.ascending:
            top_price = self.tree.keys()[0]
        else:
            top_price = self.tree.keys()[-1]
        return self.tree[top_price].head


class OrderBook:
    def __init__(self):
        self.bids = OrderTree(ascending=False)
        self.asks = OrderTree(ascending=True)
