import os
import subprocess

import utils


def get_build_path():
    return utils.get_resource_path("build")


def get_c64tass_path():
    return utils.get_resource_path(os.path.join("bins", "macos", "64tass"))


def clean_build():
    folder_path = get_build_path()
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def build(output_file_name, non_linear_prg=False):
    # -o test.prg test.asm
    command = [get_c64tass_path(), "-B"]

    if non_linear_prg:
        command.append("-n")

    command.extend(
        [
            "-L",
            f"{get_build_path()}/{output_file_name}.lst",
            "-o",
            f"{output_file_name}.prg",
            f"{get_build_path()}/{output_file_name}.asm",
        ]
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    print(f"Return code: {result.returncode}")
    print(f"Output: {result.stdout}")
    print(f"Errors: {result.stderr}")
