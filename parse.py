
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

    
    def consume(self, buffer: str) -> None:
        pos = 0

        while pos < len(buffer):
            if not self.stack:
                if buffer[pos] == '{':
                    pos += 1
                    self.stack.append({"json": {}, "partial_key": "", "state": "key", "i_state": ""})
                else:
                    print('expected to start with {')
                    assert False
            else:
                top = self.stack[-1]
                if top['state'] == 'key':
                    if top['i_state']:
                        # either get full key "thiskey"
                        # or as much as we can "thiske
                        pos += 1
                        key, pos, state = self._consume_key(buffer, pos)
                        top["partial_key"] = key
                        top["i_state"] = state

                        if state=='done':
                            # we start looking for value
                            top['state'] = 'value'
                            top['i_state'] = ''
                        if state=='colon':
                            top["state"]=''
                        
                        elif state=='end_quote':
                            pass
                    elif buffer[pos] == '"':
                        pass
                    else:
                        print('expected start quote " for key!')
                        assert False

    def _consume_key(self, s: str, pos: int):
        key = ""
        while pos < len(s):
        

        # if we see a ": we are done parsing key
        # if we see " we need to see the colon
        # if we see just text, we need to see end of quotes "

            ...
        
    def get(self) -> dict:
        """ If get's usage pattern is rare, we might want to move more complexity here"""
        return self.json



class StreamingJsonParser3:
    def __init__(self):
        # The raw data (accumulated chunks)
        self.buffer = ""
        # Current position in the buffer
        self.pos = 0
        # A stack of context dictionaries for nested objects.
        # Each context is a dict with:
        #   container: the dict being built
        #   state: one of:
        #       "start"  -- just entered an object (expecting key or close-brace)
        #       "key"    -- expecting a key (i.e. a string starting with a quote)
        #       "colon"  -- expecting a colon after a complete key
        #       "value"  -- expecting a value (which can be a string or nested object)
        #       "value_string" -- reading a string value (opening quote already consumed)
        #       "comma"  -- after a value is complete, expecting comma or closing brace
        #   current_key: the key that has been fully parsed (but its value is not yet complete)
        #   partial_string: used to accumulate a string value in progress
        self.stack = []
        # When the top-level object is complete (or partial) it is stored here.
        self.root = None

    def get(self):
        """Return the current state of the parsed JSON object (as a Python dict)."""
        return self.root

    def consume(self, chunk: str):
        self.buffer += chunk
        buf = self.buffer  # local alias for brevity
        while self.pos < len(buf):
            # If no context, we expect to start the top-level JSON object
            if not self.stack:
                self._skip_whitespace()
                if self.pos >= len(buf):
                    break
                if buf[self.pos] == "{":
                    # Begin a new object
                    self.pos += 1
                    ctx = {"container": {}, "state": "start"}
                    self.stack.append(ctx)
                    # Set the root object (even if it is not complete yet)
                    self.root = ctx["container"]
                else:
                    # Not valid input – in this simplified parser we silently stop.
                    break
            else:
                ctx = self.stack[-1]
                state = ctx["state"]
                self._skip_whitespace()
                if self.pos >= len(buf):
                    break
                ch = buf[self.pos]

                # --- State: "start" or "key" (expecting a key or the end of the object) ---
                if state in ("start", "key"):
                    if ch == "}":
                        # End of this object.
                        self.pos += 1
                        self.stack.pop()
                        if self.stack:
                            # We are inside a parent object.
                            # After a nested object completes, we set parent's state to "comma".
                            self.stack[-1]["state"] = "comma"
                        continue
                    if ch == ',':
                        # Skip comma; then expect a new key.
                        self.pos += 1
                        ctx["state"] = "key"
                        continue
                    if ch == '"':
                        # Begin reading a key.
                        key, complete = self._parse_string()
                        if not complete:
                            # Incomplete key – do not add it.
                            break
                        # Key parsed fully.
                        ctx["current_key"] = key
                        ctx["state"] = "colon"
                        continue
                    # If not a quote, then either garbage or we’re in an incomplete state.
                    break

                # --- State: "colon" (expecting a colon after a key) ---
                elif state == "colon":
                    if ch == ":":
                        self.pos += 1
                        ctx["state"] = "value"
                        continue
                    else:
                        # Waiting for colon; if not there, then incomplete.
                        break

                # --- State: "value" (expecting a value; either a string or nested object) ---
                elif state == "value":
                    if ch == '"':
                        # Value is a string.
                        # Immediately commit the key with an empty string so that even partial reads are reflected.
                        ctx["container"][ctx["current_key"]] = ""
                        ctx["partial_string"] = ""
                        self.pos += 1  # skip the opening quote
                        ctx["state"] = "value_string"
                        continue
                    elif ch == "{":
                        # Value is an object.
                        # Commit the key with an empty dict and then push a new context.
                        new_obj = {}
                        ctx["container"][ctx["current_key"]] = new_obj
                        self.pos += 1  # skip the '{'
                        new_ctx = {"container": new_obj, "state": "start"}
                        self.stack.append(new_ctx)
                        # Note: The parent's key is now fully determined.
                        # (We do not wait for the nested object to be complete.)
                        # After the nested object is finished, control will return to parent's context.
                        continue
                    else:
                        # Unexpected value start – wait for more input.
                        break

                # --- State: "value_string" (reading a string value) ---
                elif state == "value_string":
                    # Read until the closing quote.
                    # Note: since escape sequences are not handled, a quote terminates the string.
                    start = self.pos
                    while self.pos < len(buf) and buf[self.pos] != '"':
                        # Append the character to the partial string.
                        ctx["partial_string"] += buf[self.pos]
                        # Also update the value stored in the container.
                        ctx["container"][ctx["current_key"]] = ctx["partial_string"]
                        self.pos += 1
                    if self.pos >= len(buf):
                        # We reached the end of the available chunk without finding a closing quote.
                        # The partial string remains in the container.
                        break
                    else:
                        # We found the closing quote.
                        self.pos += 1  # skip the closing quote
                        # String value complete.
                        # Clean up temporary fields.
                        del ctx["partial_string"]
                        del ctx["current_key"]
                        # Now move to the "comma" state to expect a comma or a closing brace.
                        ctx["state"] = "comma"
                        continue

                # --- State: "comma" (after a key-value pair has been completed) ---
                elif state == "comma":
                    if ch == ',':
                        self.pos += 1
                        # Expect a new key next.
                        ctx["state"] = "key"
                        continue
                    elif ch == '}':
                        self.pos += 1
                        self.stack.pop()
                        if self.stack:
                            self.stack[-1]["state"] = "comma"
                        continue
                    else:
                        # Possibly incomplete – wait for more input.
                        break

                else:
                    # Unknown state.
                    break

        # Clean up consumed buffer to avoid unbounded memory growth.
        # Remove data that has been processed.
        if self.pos:
            self.buffer = self.buffer[self.pos:]
            self.pos = 0

    def _skip_whitespace(self):
        buf = self.buffer
        while self.pos < len(buf) and buf[self.pos] in " \t\r\n":
            self.pos += 1

    def _parse_string(self):
        """
        Parse a string starting at self.pos. Assumes the current character is the opening quote.
        Returns a tuple (string, complete) where complete is False if the string is incomplete.
        Note: escape sequences are not supported.
        """
        # Assume the current char is a quote; skip it.
        self.pos += 1
        result = ""
        buf = self.buffer
        while self.pos < len(buf):
            ch = buf[self.pos]
            if ch == '"':
                # End of string.
                self.pos += 1
                return result, True
            else:
                result += ch
                self.pos += 1
        # If we get here, the string is incomplete. We roll back to the opening quote
        # (i.e. do not update any state – the key is not ready yet).
        return "", False


class StreamingJsonParser:
    """
        Assumptions:
        1) In one object no two keys are the same (although that is allowed in standard)
    """
    
    START = 0
    EXPECT_KEY_OR_END = 1
    IN_KEY = 2
    EXPECT_COLON = 3
    EXPECT_VALUE = 4
    IN_STRING_VALUE = 5
    EXPECT_COMMA_OR_END = 6
    WHITESPACE = []
    
    def __init__(self):
        self.result = {}
        self.obj_stack = [self.result]  # Stack of objects being built
        self.key_stack = []  # Stack of keys to track the path
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
                            if self.key_stack:  # Make sure we have keys to pop
                                self.key_stack.pop()
                            self.state = self.EXPECT_COMMA_OR_END
            case self.IN_KEY:
                match char:
                    case '"':
                        self.state = self.EXPECT_COLON
                    case _:
                        self.current_key += char
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
                        self.key_stack.append(self.current_key)
                        self.state = self.EXPECT_KEY_OR_END
            case self.IN_STRING_VALUE:
                match char:
                    case '"':
                        self.state = self.EXPECT_COMMA_OR_END
                    case _:
                        current_obj[self.current_key] += char
            case self.EXPECT_COMMA_OR_END:
                match char:
                    case ',':
                        self.state = self.EXPECT_KEY_OR_END
                    case '}':
                        if len(self.obj_stack) > 1:  # Don't pop the root
                            self.obj_stack.pop()
                            if self.key_stack:  # Make sure we have keys to pop
                                self.key_stack.pop()
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
