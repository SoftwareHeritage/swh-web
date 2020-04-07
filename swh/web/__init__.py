from pkgutil import extend_path
from typing import Iterable

__path__ = extend_path(__path__, __name__)  # type: Iterable[str]
