import datetime, time, math, random, decimal

# MARK: Simulation Attributes
# def update_agent(agent): #Synchronize the agent times
#     global global_time
#     agent.t = global_time

# TODO: Code localized behavior
# TODO: Get financial transactions and etc. working

# MARK: Order Types
class Order:
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


# MARK: Demand Functions and Price Functions
def quintic(t, A, B, C, D, E, F): # The function type that best fits the load profiles
    return (float(decimal.Decimal(random.randrange(5, 12))/10))*(A + B*(t) + C*(t**2) + D*(t**3) + E*(t**4) + F*(t**5))

def bell_func(t, A, K, B):
    return (float(decimal.Decimal(random.randrange(9, 15))/10))*A*math.exp(-K*(t-B)**2)


# MARK: Agent Types

# TODO: Monitor the lifetime of all the orders within its ledger, if order hasn't been filled in time t, raise issue to network
class Commercial_Agent:
    def __init__(self, name, hasGen):
        self.name = str(name)
        self.type = "Commercial"
        self.hasGen = hasGen

        self.ledger = []

    def add_ledger(self, transaction):
        self.ledger.append(transaction)

    @property
    def t(self):
        now = datetime.datetime.now()
        time_ = float(str(now.hour) + '.' + str(now.minute))
        return time_

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
        return self.get_bid

    @property
    def raise_query(self):
        if self.get_net <= 0:
            return "Need power"
        elif self.get_net > 0:
            return "Want to sell power"



# MARK: Blockchain - deals with reconciling the order blocks
class Blockchain():
    def __init__(self):
        self.open_bids = {}
        self.open_asks = {}
        self.chain = []


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

    def match_orders(self): # Match the various orders on the chain
        pass

# MARK: Build the market
def build_market(n):
    agent_dict = {}
    for i in range(1, n + 1):
        agent_dict[str(i)] = Commercial_Agent(str(i), random.getrandbits(1))

    BLOCKCHAIN = Blockchain()

    timout = time.time() + 60*0.10 # block below will only run for 10 seconds
    while 1:
        if time.time() > timout:
            break

        for key, agent in agent_dict.items():
            print(agent.name, agent.get_net)
            BLOCKCHAIN.new_order(agent.get_bid)
            # print("Current state of blockchain bids: ", BLOCKCHAIN.open_bids) # Creates a lot of bid and ask objects


        print('\n')


build_market(3)












