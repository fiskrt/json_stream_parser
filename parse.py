
"""
For this task we consider a subset of JSON, where values consist solely of strings and objects. Escape sequences in strings or duplicate keys in objects are not expected.
Even if the input JSON data is incomplete, the parser should be able to return the current state of the parsed JSON object at any given point in time.
This should include partial string-values and objects, but not the keys themselves,
- i.e. `{"test": "hello", "worl` is a partial representation of `{"test": "hello"}`
- but not `{"test": "hello", "worl": ""}`.
Only once the value type of the key is determined should the parser return the key-value pair.
String values on the other hand can be partially returned: `{"test": "hello", "country": "Switzerl` is a partial representation of `{"test": "hello", "country": "Switzerl"}`.


- `__init__()`: Initializes the parser.
- `consume(buffer: str)`: Consumes a chunk of JSON data.
- `get()`: Returns the current state of the parsed JSON object as an appropriate Python object.

 """


class StreamingJsonParser2:
    """
        The 5 special characters " , : { }

        High level states:
            S) Expecting start obj {
            1) Expecting to receive a key "key":
            2) Expecting a value or a new obj start "value" or {
            3) Expecting obj done } or comma
            F) Done

    """

    def __init__(self):
        """
        Need to remember:
        1) partially created key because unless complete we don't show it 
        2) 

        """
        # stack of objects
        self.stack = []
        # JSON object created so far
        self.json = {}

    
class StreamingJsonParser:
    """
        Assumptions:
        1) In one object no two keys are the same (although that is allowed in standard)
        2) no malformed json
        3) expect one json object in stream.

        fixes:
        2) easily fixed by adding else statement for example if we are expecting a colon
        and we get anything else (non-whitespace) we raise an error.

        3) 
    """
    
    START = 0               # expect {
    EXPECT_KEY_OR_END = 1   # expect " or }
    IN_KEY = 2              # expect char or end quote "
    IN_VALUE = 3            # expect char or end quote "
    EXPECT_COLON = 4        # expect :
    EXPECT_VALUE = 5        # expect start quote "
    EXPECT_COMMA_OR_END = 6 # expect , or }
    WHITESPACE = ['\n', '\t', ' ', '\r']
    
    def __init__(self):
        self.result = {}
        self.stack = []
        self.state = self.START
        self.current_key = ""
    
    def consume(self, buffer: str) -> None:
        for c in buffer:
            if c in self.WHITESPACE and self.state not in [self.IN_KEY, self.IN_VALUE]:
                continue
            self._process_char(c)
    
    def _process_char(self, char: str) -> None:
        current_obj = self.stack[-1] if self.stack else self.result
        match self.state:
            case self.START:
                if char == '{':
                    self.state = self.EXPECT_KEY_OR_END
            case self.EXPECT_KEY_OR_END:
                if char == '"':
                    self.state = self.IN_KEY
                    self.current_key = ""
                elif char == '}':
                    if self.stack:
                        self.stack.pop()
                    self.state = self.EXPECT_COMMA_OR_END
            case self.IN_KEY:
                if char == '"':
                    self.state = self.EXPECT_COLON
                else:
                    self.current_key += char
            case self.IN_VALUE:
                if char == '"':
                    self.state = self.EXPECT_COMMA_OR_END
                else:
                    current_obj[self.current_key] += char
            case self.EXPECT_COLON:
                if char == ':':
                    self.state = self.EXPECT_VALUE
            case self.EXPECT_VALUE:
                if char == '"':
                    self.state = self.IN_VALUE
                    current_obj[self.current_key] = ""
                elif char == '{':
                    current_obj[self.current_key] = {}
                    self.stack.append(current_obj[self.current_key])
                    self.state = self.EXPECT_KEY_OR_END
            case self.EXPECT_COMMA_OR_END:
                if char == ',':
                    self.state = self.EXPECT_KEY_OR_END
                elif char == '}':
                    if self.stack:
                        self.stack.pop()
                    self.state = self.EXPECT_COMMA_OR_END 
    
    def get(self) -> dict:
        return self.result

def run_tests():
    def test_streaming_json_parser():
        parser = StreamingJsonParser()
        parser.consume('{"foo": "bar"}')
        assert parser.get() == {"foo": "bar"}

    def test_chunked_streaming_json_parser():
        parser = StreamingJsonParser()
        parser.consume('{"foo":')
        parser.consume('"bar')
        assert parser.get() == {"foo": "bar"}

    def test_partial_streaming_json_parser():
        parser = StreamingJsonParser()
        parser.consume('{"foo": "bar')
        assert parser.get() == {"foo": "bar"}

    def test4():
        parser = StreamingJsonParser()
        parser.consume('{"foo": {"bar":"')
        assert parser.get() == {"foo": {"bar":""}}

    def test5():
        parser = StreamingJsonParser()
        parser.consume('{"foo": {"ba')
        assert parser.get() == {"foo": {}}

    def test6():
        parser = StreamingJsonParser()
        parser.consume('{"foo": {"bar":"lol", "bar2":"tr')
        assert parser.get() == {"foo": {"bar": "lol", "bar2":"tr"}}
    
    def test_deep_nesting():
        """Test parsing JSON with deep (3-level) nesting."""
        parser = StreamingJsonParser()
        parser.consume('{"level1": {"level2": {"level3": "deep value"}}}')
        assert parser.get() == {"level1": {"level2": {"level3": "deep value"}}}

    def test_partial_deep_nesting():
        """Test parsing a partially complete JSON with deep nesting."""
        parser = StreamingJsonParser()
        parser.consume('{"level1": {"level2": {"level3": "partial val')
        assert parser.get() == {"level1": {"level2": {"level3": "partial val"}}}

    def test_multiple_nested_objects():
        """Test parsing JSON with multiple nested objects at the same level."""
        parser = StreamingJsonParser()
        parser.consume('{"obj1": {   "nested1": "value1"}, "obj2": {"nested2": "value2"}, "obj3": {"nested3": "value3"}}')
        expected = {
            "obj1": {"nested1": "value1"}, 
            "obj2": {"nested2": "value2"}, 
            "obj3": {"nested3": "value3"}
        }
        assert parser.get() == expected

    def test_mixed_complete_partial_objects():
        """Test parsing JSON with both complete and partial nested objects."""
        parser = StreamingJsonParser()
        parser.consume('{"complete": {"key1": "val1", "key2": "val2"}, "partial": {"key3": "val3", "key4": "incomplete')
        expected = {
            "complete": {"key1": "val1", "key2": "val2"},
            "partial": {"key3": "val3", "key4": "incomplete"}
        }
        assert parser.get() == expected

    def test_complex_incremental_parsing():
        parser = StreamingJsonParser()
        parser.consume('{')
        assert parser.get() == {}, parser.get()
        
        # Add first key and start nested object
        parser.consume('"outer1": {')
        assert parser.get() == {"outer1": {}}, parser.get()
        
        # Add key-value inside first nested object
        parser.consume('"inner1": "value1"')
        assert parser.get() == {"outer1": {"inner1": "value1"}}, parser.get()
        
        # Close first nested object, start second key and nested object
        parser.consume('}, "outer2": {')
        assert parser.get() == {"outer1": {"inner1": "value1"}, "outer2": {}}, parser.get()
        
        # Start deep nesting in second object
        parser.consume('"inner2": {"deepkey": "')
        assert parser.get() == {"outer1": {"inner1": "value1"}, "outer2": {"inner2": {"deepkey": ""}}}, parser.get()
        
        # Partially complete deep nested value
        parser.consume('deepvalue')
        assert parser.get() == {"outer1": {"inner1": "value1"}, "outer2": {"inner2": {"deepkey": "deepvalue"}}}, parser.get()
        
        # Complete all objects
        parser.consume('"}}}')
        assert parser.get() == {"outer1": {"inner1": "value1"}, "outer2": {"inner2": {"deepkey": "deepvalue"}}}, parser.get()
        
    for name, f in locals().items():
        f()
        print(f'{name} passed')
run_tests()
