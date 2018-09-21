from pydispatch import dispatcher

ORDER_CREATED_SIGNAL = 'order.created'
ORDER_STATUS_CHANGED_SIGNAL = 'order.status_changed'


class Order(object):
    def __init__(self, number):
        self.number = number
        self.status = 'PENDING'


class OrderService(object):
    """Order Service"""

    def createOrder(self, number):
        order = Order(number)
        dispatcher.send(
            signal=ORDER_CREATED_SIGNAL, sender=self, order=order
        )
        return order

    def closeOrder(self, order):
        order.status = 'CLOSED'
        dispatcher.send(
            signal=ORDER_STATUS_CHANGED_SIGNAL, sender=self, order=order
        )
        return order


# send email listener
def send_order_email_listener(sender, order):
    print("[MAIL] sending email from {} about order {}".format(
        sender, order
    ))


# send email every time when order is created
dispatcher.connect(
    send_order_email_listener,
    signal=ORDER_CREATED_SIGNAL,
    sender=dispatcher.Any
)




# let's go
s = OrderService()
o1 = s.createOrder('1234/Z/12')
o2 = s.createOrder('1234/A/12')
o3 = s.createOrder('1234/B/12')

s.closeOrder(o2)
s.closeOrder(o1)