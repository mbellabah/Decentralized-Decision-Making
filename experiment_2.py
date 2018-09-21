from pydispatch import dispatcher

SIGNAL = 'my-first-signal'

def handle_event(sender):
    print("Signal was sent by", sender)


