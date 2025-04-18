
# Current reasons why this middle layer exists:
# - Expose only the public API from the internal C++ extension module.
# - Keeping this layer enables a stable and clean interface for users.
# - Fallback mechanisms to pure Python implementation

# Underscore in _core and _json_parse to not expose them (modules ignore __all__)
try:
    from ._core import parse_json, StreamingJsonParser
except:
    print('Running the non-optimized python impl')
    from ._json_parse import parse_json, StreamingJsonParser

__all__ = ['parse_json', 'StreamingJsonParser']

# Potential future reasons:
# - To provide a clean, minimal public API, hiding internal implementation details.
# - To allow future changes to the internal module (_core) without breaking external code.
# - To enable wrapping or extending C++ functionality with Python-side logic if needed.
# - To support conditional imports or platform-specific backends if required.
# - To simplify testing by allowing the C++ layer to be mocked or swapped during tests.