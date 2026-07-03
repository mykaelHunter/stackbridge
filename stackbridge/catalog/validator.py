from stackbridge.catalog.loader import load_catalog


REQUIRED = [

    "name",

    "owner",

    "repository",

    "namespace",

]


def validate():

    services = load_catalog()["services"]

    names = set()

    for service in services:

        for field in REQUIRED:

            if field not in service:

                raise ValueError(
                    f"{service} missing {field}"
                )

        if service["name"] in names:

            raise ValueError(
                f"Duplicate service {service['name']}"
            )

        names.add(service["name"])

    return True
