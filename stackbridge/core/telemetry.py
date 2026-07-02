import json
from pathlib import Path


class Telemetry:

    def write(self, context):

        output = {

            "service": context.service,

            "environment": context.environment,

            "image": context.image,

            "duration": context.timer.elapsed(),

            "events": [

                {

                    "time": e.timestamp,

                    "event": e.name,

                    "metadata": e.metadata,

                }

                for e in context.events.events
            ],

        }

        Path(".stackbridge").mkdir(exist_ok=True)

        with open(

            ".stackbridge/deployment.json",

            "w",

        ) as f:

            json.dump(output, f, indent=2)
