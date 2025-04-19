from streamyjson import StreamingJsonParser

def run_tests():
    def test_streaming_json_parser():
        parser = StreamingJsonParser()
        parser.consume('{"foo": \n "bar"}asd')
        assert parser.get() == {"foo": "bar"}
    
    def test_streaming_json_parser2():
        parser = StreamingJsonParser()
        for c in '{"foo": "bar"}':
            parser.consume(c)
        assert parser.get() == {"foo": "bar"}

    def test_chunked_streaming_json_parser():
        parser = StreamingJsonParser()
        parser.consume('{"foo":')
        parser.consume('"bar')
        assert parser.get() == {"foo": "bar"}

    def test_partial_streaming_json_parser():
        parser = StreamingJsonParser()
        parser.consume('{"fo\\o": "bar')
        assert parser.get() == {"fo\\o": "bar"}
    
    def test3():
        parser = StreamingJsonParser()
        parser.consume('{}')
        assert parser.get() == {}

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
        print(f'[v] {name}')

if __name__ == '__main__':
    run_tests()