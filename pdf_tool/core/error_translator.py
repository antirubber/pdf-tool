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
    return FriendlyError(
        message=f"{operation} failed. Rerun with --debug for details."
    )
