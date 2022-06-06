_COUNTER: int = 0

def get() -> int:
    return _COUNTER

def increment() -> int:
    _COUNTER += 1
    return _COUNTER