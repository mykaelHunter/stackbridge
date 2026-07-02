from stackbridge.core.events import Event


class EventBus:

    def __init__(self):

        self.events = []

    def emit(self, event: Event):

        self.events.append(event)

        print(
            f"[{event.timestamp:%H:%M:%S}] "
            f"{event.type.value.upper():<12}"
            f"{event.status:<8}"
            f"{event.message}"
        )
