# August 2020, Lewis Gaul

"""
CLI entry-point.

"""

# Note: Must remain compatible with Python 3.5 so that the CLI can operate
# and report sensible errors (i.e. advise that Python 3.6+ is required).

import logging
import pathlib
import re
import subprocess as sp
import sys
import traceback
from typing import Iterable, Optional, Union

import yaml

from dcli import CLIParser, RootNode


_THIS_DIR = pathlib.Path(__file__).parent
_VENV_DIR = _THIS_DIR / ".venv"

logger = logging.getLogger(__name__)

PathLike = Union[str, pathlib.Path]


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------


class UserFacingError(Exception):
    """An error with a representation that may be shown to the user."""

    def __init__(self, msg: Optional[str] = None, *, user_msg: str, exit_code: int = 1):
        super().__init__(msg if msg else user_msg)
        self.user_msg = user_msg
        self.exit_code = exit_code


class NoVenvError(UserFacingError):
    """Virtualenv does not yet exist."""

    def __init__(self):
        super().__init__(
            user_msg="Virtual environment has not yet been set up, try running "
            "with the 'venv' arg to set it up"
        )


class NoVenvPipError(UserFacingError):
    """Virtualenv does not have pip installed properly."""


class MissingReqsError(UserFacingError):
    """Requirements are missing."""

    def __init__(self, missing: Iterable[str]):
        super().__init__(
            "The following requirements were not found: " + ", ".join(missing),
            user_msg="Not all requirements are installed, try running "
            "with the 'venv' arg to update dependencies",
        )


def _is_version_at_least(version: str, major: int, minor: Optional[int] = None) -> bool:
    """
    Check that a given version meets the minimum requirements.

    :param version:
        Version string in the form "<major>.<minor>[.<more>]"
    :param major:
        Major version requirement.
    :param minor:
        Minor version requirement, if any.
    :return:
        Whether the given version is sufficient.
    """
    parts = version.split(".", maxsplit=3)
    if int(parts[0]) < major:
        return False
    if minor and int(parts[1]) < minor:
        return False
    return True


def _find_venv_exe(path: PathLike, exe: str) -> pathlib.Path:
    """Look for executable in a venv."""
    path = pathlib.Path(path)
    if sys.platform.startswith("win"):
        if not exe.endswith(".exe"):
            exe += ".exe"
        full_path = path / "Scripts" / exe
    else:
        full_path = path / "bin" / exe
    if not full_path.is_file():
        raise FileNotFoundError("Executable not found at {}".format(full_path))
    return full_path


def _find_base_python_exe() -> pathlib.Path:
    """Look for the base python executable."""
    if hasattr(sys, "real_prefix"):
        prefix = sys.real_prefix
    else:
        prefix = sys.base_prefix
    exe = "python.exe" if sys.platform.startswith("win") else "bin/python3"
    return pathlib.Path(prefix) / exe


def _check_python_capabilities(location: Optional[PathLike] = None):
    """
    Check the basic Python capabilities (version and stdlib modules).

    :param location:
        The path to a virtualenv directory or None to check the Python in use.
    :raises FileNotFoundError:
        If a Python executable can't be found in the venv.
    :raises NoVenvPipError:
        If pip is missing from venv.
    :raises UserFacingError:
        If the Python capabilities are insufficient.
    """
    # TODO: This should be broken up into two functions.
    if location is None:
        # Check version (3.6+ required).
        version = "{v.major}.{v.minor}.{v.micro}".format(v=sys.version_info)
        if not _is_version_at_least(version, 3, 6):
            raise UserFacingError(
                user_msg="Python version 3.6+ required, detected {}".format(version)
            )
    else:
        python_exe = _find_venv_exe(location, "python")
        # Check venv Python version.
        try:
            proc = sp.run(
                [str(python_exe), "--version"],
                stdout=sp.PIPE,
                stderr=sp.PIPE,
                universal_newlines=True,
                check=True,
                timeout=1,
            )
            version = re.match(r"Python (\d\.\d+\.\d+\S*)", proc.stdout).group(1)
        except (sp.CalledProcessError, sp.TimeoutExpired):
            raise UserFacingError(user_msg="Unable to determine Python version")
        except AttributeError:
            logger.debug(
                "Unexpected output from '%s --version':\n%s", python_exe, proc.output
            )
            raise UserFacingError(user_msg="Unable to determine Python version")
        else:
            if not _is_version_at_least(version, 3, 6):
                raise UserFacingError(
                    user_msg="Python3.6+ required, detected {}".format(version)
                )
        # Check pip is available.
        try:
            pip_exe = _find_venv_exe(location, "pip")
            sp.run(
                [str(pip_exe), "--version"],
                stdout=sp.PIPE,
                stderr=sp.PIPE,
                universal_newlines=True,
                check=True,
                timeout=10,
            )
        except (FileNotFoundError, sp.CalledProcessError, sp.TimeoutExpired) as e:
            raise NoVenvPipError(
                user_msg="Pip doesn't seem to be installed into the virtual "
                "environment properly"
            ) from e


def _check_requirements(python_exe: PathLike, *, dev: bool = False):
    """
    Check the installed requirements satisfy the project requirements.

    :param python_exe:
        The path to the python executable.
    :param dev:
        Whether to include developer requirements.
    :raises UserFacingError:
        If anything goes wrong.
    :raises MissingReqsError:
        If the requirements aren't satisfied.
    """
    try:
        proc = sp.run(
            [str(python_exe), "-m", "pip", "freeze", "--all"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            check=True,
            universal_newlines=True,
            timeout=5,
        )
        installed = {
            tuple(L.lower().strip().split("==")) for L in proc.stdout.splitlines()
        }
    except Exception as e:
        raise UserFacingError(user_msg="Error checking installed packages") from e

    if dev:
        req_path = _THIS_DIR / "requirements-dev.txt"
        # TODO: Should also be checking main project reqs.
    else:
        req_path = _THIS_DIR / "requirements.txt"
    try:
        with open(req_path) as f:
            lines = {
                L.lower()
                for L in f.readlines()
                if "-r " not in L and L.strip() and not L.strip().startswith("#")
            }
        exact_requirements = {
            tuple(L.strip().split("==")[:2]) for L in lines if "==" in L
        }
        free_requirements = {L.strip() for L in lines if "==" not in L}
    except Exception as e:
        raise UserFacingError(user_msg="Error reading project requirements") from e

    missing_reqs = {
        *["==".join(r) for r in exact_requirements - installed],
        *(free_requirements - {r[0] for r in installed}),
    }
    if missing_reqs:
        raise MissingReqsError(sorted(missing_reqs))


def _check_venv(path: PathLike):
    """
    Check the given virtualenv is set up correctly.

    :param path:
        Path to virtualenv directory.
    :raises UserFacingError:
        If anything goes wrong.
    :raises NoVenvError:
        If the virtualenv doesn't exist.
    """
    path = pathlib.Path(path)
    if not path.exists():
        raise NoVenvError()
    try:
        _check_python_capabilities(path)
    except FileNotFoundError:
        raise UserFacingError(
            user_msg="There is already a '.venv' directory which doesn't seem to be "
            "a virtual environment. Can it be moved/deleted?"
        )
    except UserFacingError as e:
        raise UserFacingError(
            user_msg="There is a problem with the existing virtual environment: "
            + e.user_msg
        )


def _create_venv(path: PathLike):
    """
    Create a virtualenv.

    :param path:
        Path to virtualenv directory to create.
    :raises UserFacingError:
        If anything goes wrong.
    """
    python_exe = _find_base_python_exe()
    try:
        sp.run(
            [str(python_exe), "-m", "venv", str(path)],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            check=True,
            timeout=20,
        )
    except (sp.CalledProcessError, sp.TimeoutExpired) as e:
        raise UserFacingError(user_msg="Error creating virtual environment") from e


# ------------------------------------------------------------------------------
# Command functions
# ------------------------------------------------------------------------------


def run_app(args):
    _check_venv(_VENV_DIR)
    python_exe = _find_venv_exe(_VENV_DIR, "python")
    _check_requirements(python_exe)
    print("Run app! (not implemented)")


def make_venv(args):
    """Create or update the project virtualenv."""
    print("INFO: Checking Python capabilities...")
    _check_python_capabilities()

    if args.check:
        try:
            python_exe = _find_venv_exe(_VENV_DIR, "python")
        except FileNotFoundError:
            print(NoVenvError().user_msg)
            return 1
        try:
            _check_requirements(python_exe, dev=args.dev)
        except MissingReqsError as e:
            print(e.user_msg)
            return 1
        print("Requirements satisfied!")
        return 0

    # Create venv if it doesn't exist yet.
    try:
        _check_venv(_VENV_DIR)
        print("INFO: Found existing virtual environment")
    except NoVenvError:
        print("INFO: Creating virtual environment...")
        _create_venv(_VENV_DIR)
        print("INFO: Virtual environment successfully created")

    try:
        _check_requirements(_find_venv_exe(_VENV_DIR, "python"), dev=args.dev)
    except MissingReqsError:
        pass
    else:
        print("INFO: Requirements already satisfied")
        return 0
    # Do pip install.
    print("INFO: Checking for pip updates...")
    pip_exe = _find_venv_exe(_VENV_DIR, "pip")
    try:
        sp.run(
            [str(pip_exe), "install", "-U", "pip"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            check=True,
        )
        # TODO: Report whether pip was actually updated.
        print("INFO: pip update check was successful")
    except sp.CalledProcessError:
        raise UserFacingError(user_msg="Error checking for pip update")
    if args.dev:
        req_file = _THIS_DIR / "requirements-dev.txt"
        req_type = "developer"
    else:
        req_file = _THIS_DIR / "requirements.txt"
        req_type = "project"
    print("INFO: Installing {} requirements...".format(req_type))
    try:
        sp.run(
            [str(pip_exe), "install", "-r", str(req_file)],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            check=True,
        )
        print(
            "INFO: {} requirements successfully installed".format(req_type.capitalize())
        )
    except sp.CalledProcessError:
        raise UserFacingError(user_msg="Error installing project requirements")


def run_tests(args):
    # TODO: Need a generic way to ensure using a suitable Python executable.
    _check_venv(_VENV_DIR)
    python_exe = _find_venv_exe(_VENV_DIR, "python")
    _check_requirements(python_exe, dev=True)
    # The double dash can be used to pass args through to pytest.
    try:
        args.remaining_args.remove("--")
    except ValueError:
        pass
    if args.pytest_help:
        sp.run([str(python_exe), "-m", "pytest", "-h"])
    else:
        sp.run([str(python_exe), "-m", "pytest"] + args.remaining_args)
        # TODO: Should be passing back the exit code.


def run_bot_cli(args):
    try:
        args.remaining_args.remove("--")
    except ValueError:
        pass
    print("Running bot with:", args.remaining_args)
    print("Not implemented")


def add_bot_player(args):
    print("Adding player:", args.player_name)
    print("Not implemented")


def remove_bot_player(args):
    print("Removing player:", args.player_name)
    print("Not implemented")


_COMMANDS = {
    "run": run_app,
    "make-venv": make_venv,
    "run-tests": run_tests,
    "bump-version": lambda args: print("Not implemented"),
    "start-server": lambda args: print("Not implemented"),
    "bot": run_bot_cli,
    "bot-add-player": add_bot_player,
    "bot-remove-player": remove_bot_player,
}


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------


def _save_error_to_file(exc: Exception):
    with open(".last_error.txt", "w") as f:
        traceback.print_exception(None, exc, exc.__traceback__, file=f)


def main(argv) -> int:
    # Load the CLI schema.
    with open(str(_THIS_DIR / "cli.yaml")) as f:
        schema = RootNode.from_dict(yaml.safe_load(f))

    # Parse argv.
    prog = "run.bat" if sys.platform.startswith("win") else "run.sh"
    args = CLIParser(schema, prog=prog).parse_args(argv)
    logger.debug("Got args:", args)

    # Run the command!
    try:
        exit_code = _COMMANDS[args.command](args)
    except UserFacingError as e:
        print("ERROR:", e.user_msg, file=sys.stderr)
        _save_error_to_file(e)
        exit_code = e.exit_code
    except Exception as e:
        print(
            "ERROR: Unexpected error, please contact the maintainer to fix this!",
            file=sys.stderr,
        )
        _save_error_to_file(e)
        exit_code = 1

    if exit_code is None:
        exit_code = 0

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
