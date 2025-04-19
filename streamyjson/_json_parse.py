"""Streaming JSON parser for the following BNF:
    <json>         ::= <object>
    <object>       ::= '{' <members> '}'
    <members>      ::= ε | <member-list>
    <member-list>  ::= <member> | <member> ',' <member-list>
    <member>       ::= <string> ':' <value>
    <value>        ::= <string> | <object>
    <string>       ::= '"' <characters> '"'
    <characters>   ::= ε | <character> <characters>
    <character>    ::= any Unicode character except "

Won't write out whitespace for brevity but is allowed:
- Before and after the root object
- Around object braces
- Around colons in key-value pairs
- Around commas between members
    <whitespace>   ::= ε | <ws-char> <whitespace>
    <ws-char>      ::= ' ' | '\n' | '\t' | '\r'

NOTE: In our implemenation below if `strict_mode=False` we allow for any character until the
expected transition character is consumed. I.e <ws-char> is anything except valid terminals.
An extreme example:
    parsing random{random"hi"any characters until : is reached"val"random}random would be {"hi", "val"}
This may be a wanted or not depending on the state of the LLM. 
"""

class StreamingJsonParser:
    """
        Stack-based state machine parser of streamed JSON.
        Assumptions:
        1) In one object no two keys are the same (although that is allowed in standard)
        2) expect one json object in stream.
        3) we have that parsing '{"foo":}' is {} because we don't know the value type yet

        fixes:
        2) when stack is depth 1 and we see closing obj } we move to finished state.
        This allows us to either ignore the rest of the stream, or parse another one

        Complexity:
        Let n be the total length, d the maximum nest depth of JSON input,
        k the maximum key/value length.

        Note that d and k are both upper bounded by n.
        - time:
            O(n). (thoughts about string concats/list resizes)
        - space
            O(n). (stack just keeps REFERENCES of objects)
    """
    
    # Possible states we can be in, with their transitions explained
    START = 0               # expect {
    EXPECT_KEY_OR_END = 1   # expect " or }
    IN_KEY = 2              # expect char or end quote "
    IN_VALUE = 3            # expect char or end quote "
    EXPECT_COLON = 4        # expect :
    EXPECT_VALUE = 5        # expect start quote " or {
    EXPECT_COMMA_OR_END = 6 # expect , or }

    # WS chars we explicitly allow
    WHITESPACE = ' \n\t\r'
    EXPECTED_CHARS = {
        START: '{',
        EXPECT_KEY_OR_END: '"}',
        EXPECT_COLON: ':',
        EXPECT_VALUE: '"{',
        EXPECT_COMMA_OR_END: ',}'
    }

    def __init__(self, strict_mode:bool=False):
        self.result = {}
        self.stack = []
        self.state = self.START
        self.current_key = ""
        self.strict_mode = strict_mode
    
    def consume(self, buffer: str) -> None:
        for c in buffer:
            if c in self.WHITESPACE and self.state not in [self.IN_KEY, self.IN_VALUE]:
                continue
            if self.strict_mode:
                if self.state in self.EXPECTED_CHARS and c not in self.EXPECTED_CHARS[self.state]:
                    raise ValueError(f'Got {c} but expected {' or '.join(self.EXPECTED_CHARS[self.state])}')
            self._process_char(c)
    
    def _process_char(self, char: str) -> None:
        """
        Assertions:
        When we enter this function we are sure any VALID whitespace has been removed.

        Explaination:
        Start working on filling in the key:values of the object that has been pushed 
        the latest to the stack.

        When we finish the object with an } we then pop it off the stack and continue
        working on the previous level.
        Note that we don't have to save the finished object explicitly since we are 
        working on the self.result object in-place.
        """
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
                # Only when we start populating the VALUE we actually
                # add the key:partial_value
                if char == '"':
                    self.state = self.IN_VALUE
                    current_obj[self.current_key] = ""
                # If the value turns out to be an object we add it to stack
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

def parse_json(s: str, strict_mode=False) -> dict:
    return (
        StreamingJsonParser(strict_mode)
        .consume(s)
        .get()
    )
