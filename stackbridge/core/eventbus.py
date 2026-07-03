from stackbridge.core.events import Event


class EventBus:

    def __init__(self):

        self.events = []

    def publish(self, event):

        self.events.append(event)
        
    def all(self):

        return self.events

            

 
