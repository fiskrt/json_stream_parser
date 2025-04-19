/**
 * Test file for the C++ StreamingJsonParser
 * 
 * Compiles with:
 * g++ -std=c++17 test_json_parser.cpp -o test_json_parser -I/path/to/pybind11/include jsonparser.cpp
 */

#include "jsonparser.h"

#include <iostream>
#include <string>
#include <cassert>
#include <functional>
#include <map>

class TestSuite {
public:
    void add_test(const std::string& name, std::function<void()> test) {
        tests[name] = test;
    }
    
    void run_all() {
        int passed = 0;
        int failed = 0;
        
        for (const auto& [name, test] : tests) {
            try {
                test();
                std::cout << "[PASS] " << name << std::endl;
                passed++;
            } catch (const std::exception& e) {
                std::cout << "[FAIL] " << name << ": " << e.what() << std::endl;
                failed++;
            }
        }
        
        std::cout << "\nResults: " << passed << " passed, " << failed << " failed" << std::endl;
    }
    
private:
    std::map<std::string, std::function<void()>> tests;
};

// Check if two py::dict objects are equal
bool dicts_equal(const py::dict& a, const py::dict& b) {
    if (a.size() != b.size()) return false;
    
    for (auto item : a) {
        std::string key = py::str(item.first);
        if (!b.contains(item.first)) return false;
        
        py::object a_val = item.second;
        py::object b_val = b[item.first];
        
        // Check if the values are dictionaries
        if (py::isinstance<py::dict>(a_val) && py::isinstance<py::dict>(b_val)) {
            if (!dicts_equal(a_val.cast<py::dict>(), b_val.cast<py::dict>())) return false;
        }
        // Check if the values are strings
        else if (py::isinstance<py::str>(a_val) && py::isinstance<py::str>(b_val)) {
            if (std::string(py::str(a_val)) != std::string(py::str(b_val))) return false;
        }
        else {
            return false;
        }
    }
    return true;
}

// Create expected dictionaries using pybind11
py::dict create_expected_dict(const std::map<std::string, py::object>& items) {
    py::dict result;
    for (const auto& [key, value] : items) {
        result[py::str(key)] = value;
    }
    return result;
}

py::dict create_nested_dict(const std::map<std::string, py::object>& items) {
    return create_expected_dict(items);
}

int main() {
    TestSuite suite;
    
    // Basic parsing test
    suite.add_test("test_basic_json", []() {
        StreamingJsonParser parser;
        parser.consume("{\"foo\": \"bar\"}");
        
        py::dict expected;
        expected["foo"] = py::str("bar");
        
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected));
    });
    
    // Test parsing in chunks
    suite.add_test("test_chunked_parsing", []() {
        StreamingJsonParser parser;
        parser.consume("{\"foo\":");
        parser.consume("\"bar\"}");
        
        py::dict expected;
        expected["foo"] = py::str("bar");
        
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected));
    });
    
    // Test character-by-character parsing
    suite.add_test("test_char_by_char_parsing", []() {
        StreamingJsonParser parser;
        std::string json = "{\"foo\": \"bar\"}";
        for (char c : json) {
            parser.consume(std::string(1, c));
        }
        
        py::dict expected;
        expected["foo"] = py::str("bar");
        
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected));
    });
    
    // Test empty object
    suite.add_test("test_empty_object", []() {
        StreamingJsonParser parser;
        parser.consume("{}");
        
        py::dict expected;
        
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected));
    });
    
    // Test partial string value
    suite.add_test("test_partial_string", []() {
        StreamingJsonParser parser;
        parser.consume("{\"foo\": \"partial");
        
        py::dict expected;
        expected["foo"] = py::str("partial");
        
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected));
    });
    
    // Test nested objects
    suite.add_test("test_nested_objects", []() {
        StreamingJsonParser parser;
        parser.consume("{\"foo\": {\"bar\":\"value\"}}");
        
        py::dict inner;
        inner["bar"] = py::str("value");
        
        py::dict expected;
        expected["foo"] = inner;
        
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected));
    });
    
    // Test partial nested objects
    suite.add_test("test_partial_nested", []() {
        StreamingJsonParser parser;
        parser.consume("{\"foo\": {\"bar\":\"");
        
        py::dict inner;
        inner["bar"] = py::str("");
        
        py::dict expected;
        expected["foo"] = inner;
        
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected));
    });
    
    // Test multiple key-value pairs
    suite.add_test("test_multiple_keys", []() {
        StreamingJsonParser parser;
        parser.consume("{\"key1\": \"value1\", \"key2\": \"value2\"}");
        
        py::dict expected;
        expected["key1"] = py::str("value1");
        expected["key2"] = py::str("value2");
        
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected));
    });
    
    // Test deep nesting
    suite.add_test("test_deep_nesting", []() {
        StreamingJsonParser parser;
        parser.consume("{\"level1\": {\"level2\": {\"level3\": \"deep value\"}}}");
        
        py::dict level3;
        level3["level3"] = py::str("deep value");
        
        py::dict level2;
        level2["level2"] = level3;
        
        py::dict expected;
        expected["level1"] = level2;
        
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected));
    });
    
    // Test complex incremental parsing
    suite.add_test("test_complex_incremental", []() {
        StreamingJsonParser parser;
        
        // Start with empty object
        parser.consume("{");
        py::dict expected1;
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected1));
        
        // Add first key and start nested object
        parser.consume("\"outer1\": {");
        py::dict inner1;
        py::dict expected2;
        expected2["outer1"] = inner1;
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected2));
        
        // Add key-value inside first nested object
        parser.consume("\"inner1\": \"value1\"");
        py::dict inner1_updated;
        inner1_updated["inner1"] = py::str("value1");
        py::dict expected3;
        expected3["outer1"] = inner1_updated;
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected3));
        
        // Close first nested object, start second key and nested object
        parser.consume("}, \"outer2\": {");
        py::dict inner2;
        py::dict expected4;
        expected4["outer1"] = inner1_updated;
        expected4["outer2"] = inner2;
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected4));
        
        // Complete all objects
        parser.consume("\"inner2\": \"value2\"}}");
        py::dict inner2_updated;
        inner2_updated["inner2"] = py::str("value2");
        py::dict expected5;
        expected5["outer1"] = inner1_updated;
        expected5["outer2"] = inner2_updated;
        assert(dicts_equal(parser.getPython().cast<py::dict>(), expected5));
    });
    
    suite.run_all();
    
    return 0;
}