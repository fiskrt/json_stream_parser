
/**
* StreamingJsonParser: A C++ implementation of a streaming JSON parser.
* With Python bindings using pybind11.
*/
#pragma once

#include <string>
#include <unordered_map>
#include <vector>
#include <memory>
#include <pybind11/pybind11.h>

namespace py = pybind11;

class JsonValue;
class JsonString;
class JsonObject;

/**
Our JSON values are defined by classes JsonString and 
JsonObject where both are derived from JsonValue.

JSON keys are always strings so we use std::string for those.
It's also easy to convert to python types using py::str.
*/
class JsonValue {
public:
    virtual ~JsonValue() = default;
    virtual bool isString() const = 0;
    virtual bool isObject() const = 0;
    virtual py::object toPython() const = 0;
};

/**
* String value in JSON
*/
class JsonString : public JsonValue {
public:
    JsonString(const std::string& value = "") : value(value) {}
    
    bool isString() const override { return true; }
    bool isObject() const override { return false; }
    
    void append(char c) { value += c; }
    
    py::object toPython() const override {
        return py::str(value);
    }
    
private:
    std::string value;
};

/**
* Object value in JSON (collection of key-value pairs)
*/
class JsonObject : public JsonValue {
public:
    bool isString() const override { return false; }
    bool isObject() const override { return true; }
    
    // Add a key-value pair
    void set(const std::string& key, std::unique_ptr<JsonValue> value) {
        members[key] = std::move(value);
    }
    
    // Check if a key exists
    bool has(const std::string& key) const {
        return members.find(key) != members.end();
    }
    
    // Get a value by key
    JsonValue* get(const std::string& key) {
        auto it = members.find(key);
        return it != members.end() ? it->second.get() : nullptr;
    }
    
    // Construct a python dictionary with py::objects as keys and values.
    py::object toPython() const override {
        py::dict result;
        for (const auto& [key, value] : members) {
            result[py::str(key)] = value->toPython();
        }
        return result;
    }
    
private:
    std::unordered_map<std::string, std::unique_ptr<JsonValue>> members;
};

/**
* Stack-based state machine parser for streaming JSON.
*/
class StreamingJsonParser {
public:
    // Possible states in the parsing state machine
    enum State {
        START = 0,               // expect {
        EXPECT_KEY_OR_END = 1,   // expect " or }
        IN_KEY = 2,              // expect char or end quote "
        IN_VALUE = 3,            // expect char or end quote "
        EXPECT_COLON = 4,        // expect :
        EXPECT_VALUE = 5,        // expect start quote " or {
        EXPECT_COMMA_OR_END = 6  // expect , or }
    };
    
    StreamingJsonParser(bool strict_mode = false);
    ~StreamingJsonParser() = default;
    
    void consume(const std::string& buffer);
    
    // Don't confuse StreamingJsonParser::get and std::unqiue_ptr::get
    JsonObject* get() const {
        return result.get();
    }
    
    // Get the result as a Python dict
    py::object getPython() const {
        return result->toPython();
    }
    
private:
    std::unique_ptr<JsonObject> result;
    // Holds a stack of pointers to JsonObjects, make sure that pointers pushed
    // here have lifetimes that exceed the time on stack.
    std::vector<JsonObject*> stack;
    State state;
    std::string current_key;
    bool strict_mode;
    std::unordered_map<State, std::string> expected_chars;
    
    bool isWhitespace(char c) const;
    void processChar(char c);
};
