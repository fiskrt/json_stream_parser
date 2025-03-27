
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
        2) no whitespace
        3) no malformed json
    """
    
    START = 0
    EXPECT_KEY_OR_END = 1
    IN_KEY = 2
    EXPECT_COLON = 3
    EXPECT_VALUE = 4
    IN_STRING_VALUE = 5
    EXPECT_COMMA_OR_END = 6
    
    def __init__(self):
        self.result = {}
        self.obj_stack = [self.result]
        self.state = self.START
        self.current_key = ""
    
    def consume(self, buffer: str) -> None:
        for c in buffer:
            self._process_char(c)
    
    def _process_char(self, char: str) -> None:
        current_obj = self.obj_stack[-1]
        match self.state:
            case self.START:
                if char == '{':
                    self.state = self.EXPECT_KEY_OR_END
            case self.EXPECT_KEY_OR_END:
                match char:
                    case '"':
                        self.state = self.IN_KEY
                        self.current_key = ""
                    case '}':
                        if len(self.obj_stack) > 1:  # Don't pop the root
                            self.obj_stack.pop()
                            self.state = self.EXPECT_COMMA_OR_END
            case self.IN_KEY:
                match char:
                    case '"': self.state = self.EXPECT_COLON
                    case _: self.current_key += char
            case self.EXPECT_COLON:
                if char == ':':
                    self.state = self.EXPECT_VALUE
            case self.EXPECT_VALUE:
                match char:
                    case '"':
                        self.state = self.IN_STRING_VALUE
                        current_obj[self.current_key] = ""
                    case '{':
                        current_obj[self.current_key] = {}
                        self.obj_stack.append(current_obj[self.current_key])
                        self.state = self.EXPECT_KEY_OR_END
            case self.IN_STRING_VALUE:
                match char:
                    case '"': self.state = self.EXPECT_COMMA_OR_END
                    case _: current_obj[self.current_key] += char
            case self.EXPECT_COMMA_OR_END:
                match char:
                    case ',': self.state = self.EXPECT_KEY_OR_END
                    case '}':
                        if len(self.obj_stack) > 1:  # Don't pop the root
                            self.obj_stack.pop()
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
        print(parser.get())
        assert parser.get() == {"foo": {"bar":""}}

    def test5():
        parser = StreamingJsonParser()
        parser.consume('{"foo": {"ba')
        assert parser.get() == {"foo": {}}

    def test6():
        parser = StreamingJsonParser()
        parser.consume('{"foo": {"bar":"lol", "bar2":"tr')
        print(parser.get())
        assert parser.get() == {"foo": {"bar": "lol", "bar2":"tr"}}
    
    def test_deep_nesting():
        """Test parsing JSON with deep (3-level) nesting."""
        parser = StreamingJsonParser()
        parser.consume('{"level1": {"level2": {"level3": "deep value"}}}')
        assert parser.get() == {"level1": {"level2": {"level3": "deep value"}}}
        print("Test deep nesting passed!")

    def test_partial_deep_nesting():
        """Test parsing a partially complete JSON with deep nesting."""
        parser = StreamingJsonParser()
        parser.consume('{"level1": {"level2": {"level3": "partial val')
        assert parser.get() == {"level1": {"level2": {"level3": "partial val"}}}
        print("Test partial deep nesting passed!")

    def test_multiple_nested_objects():
        """Test parsing JSON with multiple nested objects at the same level."""
        parser = StreamingJsonParser()
        parser.consume('{"obj1": {"nested1": "value1"}, "obj2": {"nested2": "value2"}, "obj3": {"nested3": "value3"}}')
        expected = {
            "obj1": {"nested1": "value1"}, 
            "obj2": {"nested2": "value2"}, 
            "obj3": {"nested3": "value3"}
        }
        assert parser.get() == expected
        print("Test multiple nested objects passed!")

    def test_mixed_complete_partial_objects():
        """Test parsing JSON with both complete and partial nested objects."""
        parser = StreamingJsonParser()
        parser.consume('{"complete": {"key1": "val1", "key2": "val2"}, "partial": {"key3": "val3", "key4": "incomplete')
        expected = {
            "complete": {"key1": "val1", "key2": "val2"},
            "partial": {"key3": "val3", "key4": "incomplete"}
        }
        assert parser.get() == expected
        print("Test mixed complete and partial objects passed!")

    def test_complex_incremental_parsing():
        parser = StreamingJsonParser()
        
        # Start with an empty object
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
        
        print("Test complex incremental parsing passed!")
    for f in locals().values():
        f()
run_tests()
