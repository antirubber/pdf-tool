from dataclasses import dataclass


@dataclass(frozen=True)
class PikepdfFailure:
    exception_name: str
    message: str = ""


@dataclass(frozen=True)
class SubprocessFailure:
    binary: str
    exit_code: int
    stderr: str = ""


BackendFailure = PikepdfFailure | SubprocessFailure


class BackendError(Exception):
    def __init__(self, failure: BackendFailure):
        super().__init__(str(failure))
        self.failure = failure


@dataclass(frozen=True)
class FriendlyError:
    message: str
    suggested_action: str | None = None


def translate(operation: str, failure: BackendFailure) -> FriendlyError:
    match failure:
        case PikepdfFailure(exception_name="PasswordError"):
            return FriendlyError(message="Wrong password.")
        case PikepdfFailure(exception_name="ValueError", message=m) if (
            "overwrite input file" in m
        ):
            return FriendlyError(
                message="The output path is the same as the input file.",
                suggested_action="Choose a different output path.",
            )
        case SubprocessFailure(exit_code=-1, stderr=s) if "not found" in s:
            return FriendlyError(
                message=f"{failure.binary} is not installed.",
                suggested_action=f"Install {failure.binary} to use this operation.",
            )
        case SubprocessFailure(exit_code=-1, stderr=s) if "timed out" in s:
            return FriendlyError(
                message=f"{failure.binary} timed out before it finished.",
                suggested_action="Try again with a smaller or simpler file.",
            )
    return FriendlyError(
        message=f"{operation} failed. Rerun with --debug for details."
    )
