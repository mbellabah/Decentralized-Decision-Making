from pydispatch import dispatcher
import threading
import datetime, time, math, random, decimal


# TODO: Code localized behavior
# TODO: Get financial transactions and etc. working
# TODO: Get the threading and dispatcher working

# MARK: Signal and Senders
BLOCKCHAIN_SIGNAL = 'blockchain.signal'
BLOCKCHAIN_SENDER = 'blockchain.sender'
ORDER_CREATED_SIGNAL = 'order.created'
ORDER_STATUS_CHANGED_SIGNAL = 'order.status_changed'


# MARK: Order Types
class Order(object):
    tag = 0
    def __init__(self, sender, quantity, price):
        Order.tag += 1
        self.id = Order.tag
        self.time_stamp = datetime.datetime.now()
        self.life_time = 0

        self.sender = sender
        self.quantity = quantity
        self.price = price
        self.open = True

    def __sub__(self, other):
        return self.quantity - other.quantity

    def __str__(self):
        return str(self.get_id())

    # SETTERS
    def close_order(self):
        self.open =  False

    # GETTERS
    def get_time_stamp(self):
        return self.time_stamp
    def get_id(self):
        return str(self.id).zfill(5)
    def get_lifetime(self):
        self.life_time = datetime.datetime.now().second - self.time_stamp.second
        return self.life_time
    def get_quantity(self):
        return self.quantity
    def get_price(self):
        return self.price
    def get_sender(self):
        return self.sender

class Bid(Order):
    def __init__(self, sender, quantity, price):
        Order.__init__(self, sender, quantity, price)
        self.type = "Bid"

    # GETTERS
    def get_type(self):
        return self.type

class Ask(Order):
    def __init__(self, sender, quantity, price):
        Order.__init__(self, sender, quantity, price)
        self.type = "Ask"

    # GETTERS
    def get_type(self):
        return self.type

class Transaction():
    # Takes in an ask and bid object
    def __init__(self, ask, bid, settled_price, settled_quantity):
        self.ask_ref = ask.get_sender()
        self.bid_ref = bid.get_sender()

        self.settled_price = settled_price
        self.quantity = settled_quantity

        self.value = self.settled_price * self.quantity

    def __repr__(self):
        return " {} {} {} {}".format(self.bid_ref, self.ask_ref, self.settled_price, self.quantity)


# MARK: Demand Functions and Price Functions
def quintic(t, A, B, C, D, E, F): # The function type that best fits the load profiles
    # return (float(decimal.Decimal(random.randrange(5, 12))/10))*(A + B*(t) + C*(t**2) + D*(t**3) + E*(t**4) + F*(t**5))
    return float(A + B * (t) + C * (t ** 2) + D * (t ** 3) + E * (t ** 4) + F * (t ** 5))
def bell_func(t, A, K, B):
    '''Solar panel generation'''
    # return (float(decimal.Decimal(random.randrange(9, 15))/10))*A*math.exp(-K*(t-B)**2)
    # return float(A*math.exp(-K*(t-B)**2))
    return 300 #TODO: Remove, and change to the previous return statements


# MARK: Agent Types

class Commercial_Agent:
    def __init__(self, name, hasGen):
        self.name = str(name)
        self.type = "Commercial"
        self.hasGen = hasGen
        self.ledger = []

        self.send_order()


    def send_order(self):
        '''Will send an order to the blockchain bus - doesn't need to be prodded'''
        while 1:
            order = None
            current_net = self.get_net
            if current_net <= 0:
                order = Bid(self.name, current_net, self.determine_price())
            else:
                order = Ask(self.name, current_net, self.determine_price())

            if order.get_type() == "Bid":
                print("Agent {0} WANTS {1} at price ${2}. Solar panel? {3}".format(
                    self.name,
                    order.get_quantity(),
                    order.get_price(),
                    bool(self.hasGen)
                ))
            else:
                print("Agent {0} ASKS {1} at price ${2}. Solar panel? {3}".format(
                    self.name,
                    order.get_quantity(),
                    order.get_price(),
                    bool(self.hasGen)
                ))

            dispatcher.send(
                signal=ORDER_CREATED_SIGNAL,
                sender=self,
                order=order
            )

            # ----------------------------#
            self.aknowledged_order_listener()
            time.sleep(1)



    def aknowledged_order_listener(self):

        def transaction_listener(self, sender, transaction):
            print("Agent {0} received confirmation {1} from {2}".format(
                self.name,
                transaction,
                sender
            ))

        dispatcher.connect(
            transaction_listener,
            signal=BLOCKCHAIN_SIGNAL,
            sender=BLOCKCHAIN_SENDER
        )

    def add_ledger(self, transaction):
        self.ledger.append(transaction)

    @property
    def t(self):
        now = datetime.datetime.now()
        return float(str(now.hour) + '.' + str(now.minute))

    def determine_price(self):
        return self.t/100 + 0.1

    @property
    def get_bid(self):
        price, quantity = self.determine_price(), quintic(self.t, 116.06, -50.67, 21.861, -2.554, 0.1189, -0.001962)
        return Bid(self.name, quantity, price)

    @property
    def get_ask(self):
        # TODO: Later accomodate for battery storage or some other form of excess energy in a strictly consumer building
        if self.hasGen:
            price, quantity = self.t/100 + 0.1, bell_func(self.t, 300, 0.0666666, 13)
            return Ask(self.name, quantity, price)

    @property
    def get_net(self):
        bid_quantity = quintic(self.t, 116.06, -50.67, 21.861, -2.554, 0.1189, -0.001962)
        if self.hasGen:
            return bell_func(self.t, 300, 0.0666666, 13) - bid_quantity
        return -bid_quantity # Note the negative


# MARK: Blockchain - deals with reconciling the order blocks
class Blockchain():
    def __init__(self):
        self.open_bids = {}
        self.open_asks = {}
        self.chain = []

        self.receive_order() # Will receive any new orders sent by agents on network

    def receive_order(self):
        while 1:
            dispatcher.connect(
                self.blockchain_order_listener,
                signal=ORDER_CREATED_SIGNAL,
                sender=dispatcher.Any
            )

    def blockchain_order_listener(self, sender, order): # order object
        order_type = order.get_type()

        print("Blockchain received order: {} of type: {} for price ${} and quantity {} from sender: Agent {}".format(
            order,
            order_type,
            order.get_price(),
            order.get_quantity(),
            sender.name
        ))

        self.add_order(order)

        if order_type == "Bid":
            transaction = self.match_order(order)
            self.blockchain_confirm_transaction(transaction)
        elif order_type == "Ask":
            pass

        time.sleep(1)

    def blockchain_confirm_transaction(self, transaction):
        dispatcher.send(
            transaction=transaction,
            signal=BLOCKCHAIN_SIGNAL,
            sender=BLOCKCHAIN_SENDER
        )
        time.sleep(0.5)

    @property
    def length(self):
        return len(self.chain)

    def add_order(self, order):
        if order is not None:
            if order.get_type() == "Bid":
                self.open_bids[order.get_id()] = order

            elif order.get_type() == "Ask":
                self.open_asks[order.get_id()] = order
            self.chain.append(order)
        else:
            pass

    def strike_order(self, order):
        if order is not None:
            if order.get_type() == "Bid":
                self.open_bids.pop(order.get_id())

            elif order.get_type() == "Ask":
                self.open_asks.pop(order.get_id())
            self.chain.remove(order)
        else:
            pass

    # TODO: Must send the confirmation that transaction has been fulfilled to the relevant agents
    # TODO: Fix transaction, currently sending None
    def match_order(self, bid): # Match a bid
        bid_q = bid.get_quantity()
        bid_p = bid.get_price()

        # Be within 5% of quantity and 10% of price
        dq = .05 * bid_q; dp = 0.5*bid_p

        open_asks_copy = self.open_asks.copy()

        for a_key, ask in open_asks_copy.items():
            ask_q, ask_p = ask.get_quantity(), ask.get_price()

            # TODO: Change, we ideally want ask_q and bid_q to be within some x of each other, rather than the binary comparison below
            if ask_q > abs(bid_q) and abs(ask_p - bid_p) <= dp:
                # Strike the orders
                self.strike_order(ask)
                self.strike_order(bid)
                return Transaction(ask, bid, bid_p, bid_q)

            else: pass

# MARK: Build the market
def build_market(n):

    agent_threads = []
    for i in range(1, n+1):
        t = threading.Thread(target = Commercial_Agent, args=(str(i), random.getrandbits(1)))
        agent_threads.append(t)
        t.start()

    blockchain_thread = threading.Thread(target=Blockchain)
    blockchain_thread.start()

if __name__ == "__main__":
    build_market(3)