import subprocess


def commit(service, version):

    subprocess.run(
        ["git", "add", "."],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"Deploy {service} {version}",
        ],
        check=True,
    )

    subprocess.run(
        ["git", "push"],
        check=True,
    )
