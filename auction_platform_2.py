from pydispatch import dispatcher
import threading
import datetime, time, math, random, decimal


# TODO: Code localized behavior
# TODO: Get financial transactions and etc. working
# TODO: Get the threading and dispatcher working

# MARK: Signal and Senders
AGENT_SIGNAL = 'agent_signal'
AGENT_SENDER = 'agent_sender'
BLOCKCHAIN_SIGNAL = 'blockchain_signal'
BLOCKCHAIN_SENDER = 'blockchain_sender'

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
    # return (float(decimal.Decimal(random.randrange(9, 15))/10))*A*math.exp(-K*(t-B)**2)
    return float(A*math.exp(-K*(t-B)**2))


# MARK: Agent Types

# TODO: Monitor the lifetime of all the orders within its ledger, if order hasn't been filled in time t, raise issue to network
class Commercial_Agent:
    def __init__(self, name, hasGen):
        self.name = str(name)
        self.type = "Commercial"
        self.hasGen = hasGen
        self.ledger = []

        dispatcher.connect(self.agent_dispatcher_receive, signal=BLOCKCHAIN_SIGNAL, sender=BLOCKCHAIN_SENDER)
        self.raise_query() # Run the agent module's behavior in a separate thread

    def agent_dispatcher_receive(self, message):
        '''handle dispatcher'''
        print("Commercial agent {} has received message: {}".format(self.name, message))
        current_net = self.get_net
        reply = None
        if current_net <= 0: # Returns a bid/ask for the amount
            reply = self.get_bid
        if current_net > 0:
            reply = self.get_ask

        # Send to the dispatcher bus the order and the add to the ledger
        dispatcher.send(message=reply, signal=AGENT_SIGNAL, sender=AGENT_SENDER)
        if reply is not None:
            self.ledger.append(reply)

    def raise_query(self):
        '''loop and raise_query'''
        while 1:
            current_net = self.get_net
            if current_net <= 0:
                print("Agent {} WANTS {} power, solar panel: {}".format(self.name, current_net, bool(self.hasGen)))
            else:
                pass
            time.sleep(1)

    def add_ledger(self, transaction):
        self.ledger.append(transaction)

    @property
    def t(self):
        now = datetime.datetime.now()
        return float(str(now.hour) + '.' + str(now.minute))

    @property
    def get_bid(self):
        price, quantity = self.t/100 + 0.1, quintic(self.t, 116.06, -50.67, 21.861, -2.554, 0.1189, -0.001962)
        return Bid(self.name, quantity, price)

    @property
    def get_ask(self):
        if self.hasGen:
            price, quantity = self.t/100 + 0.1, bell_func(self.t, 300, 0.0666666, 13)
            return Ask(self.name, quantity, price)

    @property
    def get_net(self):
        if self.hasGen:
            return self.get_ask - self.get_bid
        return -self.get_bid.quantity # Note the negative


# MARK: Blockchain - deals with reconciling the order blocks
class Blockchain():
    def __init__(self):
        self.open_bids = {}
        self.open_asks = {}
        self.chain = []

        dispatcher.connect(self.blockchain_dispatcher_receive_order, signal=AGENT_SIGNAL, sender=AGENT_SENDER)
        self.blockchain_poll()

    def blockchain_dispatcher_receive_order(self, message): # Message is an order object
        if message is not None:
            print("Blockchain has received message: {} from sender-agent {}".format(message, message.get_sender()))
            self.new_order(message)
            print("Current Open_BIDS = ", self.open_bids)

    def blockchain_poll(self):
        while 1:
            dispatcher.send(message=None, signal=BLOCKCHAIN_SIGNAL, sender=BLOCKCHAIN_SENDER)
            time.sleep(2)

    @property
    def length(self):
        return len(self.chain)

    def new_order(self, order):
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
    def match_orders(self, bid, open_asks): # Match a bid
        bid_q = bid.get_quantity()
        bid_p = bid.get_price

        # Be within 5% of quantity and 10% of price
        dq = .05 * bid_q
        dp = .10 * bid_p

        for a_key, ask in open_asks.items():
            ask_q, ask_p = ask.get_quantity(), ask.get_price()

            if abs(ask_q - bid_q) <= dq and abs(ask_p - bid_p) <= dp:
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

    blockchain_thread = threading.Thread(target = Blockchain)
    blockchain_thread.start()

if __name__ == "__main__":
    build_market(2)













