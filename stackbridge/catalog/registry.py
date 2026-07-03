from stackbridge.catalog.loader import load_catalog


class ServiceRegistry:

    def __init__(self):

        self.catalog = load_catalog()["services"]

    def list(self):

        return self.catalog

    def get(self, name):

        for service in self.catalog:

            if service["name"] == name:
                return service

        return None
