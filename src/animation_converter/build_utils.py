import os
import platform
import subprocess

from logger import get_logger
import utils

logger = get_logger()


def get_build_path():
    return utils.get_resource_path("build")


def get_c64tass_path():
    """Get the correct 64tass binary path based on the current operating system."""
    system = platform.system().lower()

    # Map platform.system() output to our directory names
    if system == "darwin":
        platform_dir = "macos"
        binary_name = "64tass"
    elif system == "linux":
        platform_dir = "linux"
        binary_name = "64tass"
    elif system == "windows":
        platform_dir = "windows"
        binary_name = "64tass.exe"
    else:
        # Fallback to linux for unknown systems
        logger.warning(f"Unknown platform '{system}', defaulting to linux binary")
        platform_dir = "linux"
        binary_name = "64tass"

    binary_path = utils.get_resource_path(
        os.path.join("bins", platform_dir, binary_name)
    )

    # Verify the binary exists
    if not os.path.exists(binary_path):
        raise FileNotFoundError(f"64tass binary not found at {binary_path}")

    # Make sure the binary is executable on Unix-like systems
    if platform_dir in ["macos", "linux"]:
        try:
            os.chmod(binary_path, 0o755)
        except PermissionError:
            logger.warning(f"Could not make {binary_path} executable")

    logger.debug(f"Using 64tass binary: {binary_path}")
    return binary_path


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
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        logger.success(f"Build successful: {output_file_name}.prg")
        logger.debug(f"Output: {result.stdout}")
    else:
        logger.error(f"Build failed with return code: {result.returncode}")
        logger.error(f"Output: {result.stdout}")
        logger.error(f"Errors: {result.stderr}")
