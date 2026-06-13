import subprocess


def terraform_init():
    subprocess.run(
        ["terraform", "init"],
        check=True
    )


def terraform_apply():
    subprocess.run(
        ["terraform", "apply", "-auto-approve"],
        check=True
    )


def terraform_destroy():
    subprocess.run(
        ["terraform", "destroy", "-auto-approve"],
        check=True
    )
