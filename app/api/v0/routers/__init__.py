import sys

from slowapi import Limiter
from slowapi.util import get_remote_address

if "pytest" in sys.modules:
    limiter = Limiter(key_func=get_remote_address, enabled=False)
else:
    limiter = Limiter(key_func=get_remote_address)
