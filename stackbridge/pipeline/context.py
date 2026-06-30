class DeploymentContext:

    def __init__(self, service, environment):

        self.service = service
        self.environment = environment

        self.image = None

        self.config = None

        self.logger = None

        self.timer = None
