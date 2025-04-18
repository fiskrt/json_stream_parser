/**
* StreamingJsonParser: A C++ implementation of a streaming JSON parser.
* With Python bindings using pybind11.
*/

#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
#include <memory>
#include <stdexcept>
#include <cassert>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

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
    
    std::string& getValue() { return value; }
    const std::string& getValue() const { return value; }
    
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
    
    StreamingJsonParser(bool strict_mode = false) 
        : state(START), strict_mode(strict_mode), result(new JsonObject()) {
        // Initialize the expected characters for each state
        expected_chars[START] = "{";
        expected_chars[EXPECT_KEY_OR_END] = "\"}";
        expected_chars[EXPECT_COLON] = ":";
        expected_chars[EXPECT_VALUE] = "\"{";
        expected_chars[EXPECT_COMMA_OR_END] = ",}";
    }
    
    ~StreamingJsonParser() = default;
    
    void consume(const std::string& buffer) {
        for (char c : buffer) {
            if (isWhitespace(c) && state != IN_KEY && state != IN_VALUE) {
                continue;
            }
            
            if (strict_mode) {
                auto it = expected_chars.find(state);
                if (it != expected_chars.end() && it->second.find(c) == std::string::npos) {
                    throw std::runtime_error(
                        "Got " + std::string(1, c) + " but expected one of " + it->second
                    );
                }
            }
            
            processChar(c);
        }
    }
    
    // TODO: don't use ::get
    JsonObject* get() const {
        return dynamic_cast<JsonObject*>(result.get());
    }
    
    // Get the result as a Python dict
    py::object getPython() const {
        return result->toPython();
    }
    
private:
    std::unique_ptr<JsonValue> result;
    std::vector<JsonObject*> stack;
    State state;
    std::string current_key;
    bool strict_mode;
    std::unordered_map<State, std::string> expected_chars;
    
    bool isWhitespace(char c) const {
        return c == ' ' || c == '\n' || c == '\t' || c == '\r';
    }
    
    void processChar(char c) {
        JsonObject* current_obj = stack.empty() ? 
                                dynamic_cast<JsonObject*>(result.get()) : 
                                stack.back();
        
        switch (state) {
            case START:
                if (c == '{') {
                    state = EXPECT_KEY_OR_END;
                }
                break;
                
            case EXPECT_KEY_OR_END:
                if (c == '"') {
                    state = IN_KEY;
                    current_key = "";
                } else if (c == '}') {
                    if (!stack.empty()) {
                        stack.pop_back();
                    }
                    state = EXPECT_COMMA_OR_END;
                }
                break;
                
            case IN_KEY:
                if (c == '"') {
                    state = EXPECT_COLON;
                } else {
                    current_key += c;
                }
                break;
                
            case IN_VALUE:
                if (c == '"') {
                    state = EXPECT_COMMA_OR_END;
                } else {
                    auto* value = current_obj->get(current_key);
                    if (value && value->isString()) {
                        dynamic_cast<JsonString*>(value)->getValue() += c;
                    }
                }
                break;
                
            case EXPECT_COLON:
                if (c == ':') {
                    state = EXPECT_VALUE;
                }
                break;
                
            case EXPECT_VALUE:
                if (c == '"') {
                    state = IN_VALUE;
                    current_obj->set(current_key, std::make_unique<JsonString>());
                } else if (c == '{') {
                    auto newObj = std::make_unique<JsonObject>();
                    JsonObject* objPtr = dynamic_cast<JsonObject*>(newObj.get());
                    current_obj->set(current_key, std::move(newObj));
                    stack.push_back(objPtr);
                    state = EXPECT_KEY_OR_END;
                }
                break;
                
            case EXPECT_COMMA_OR_END:
                if (c == ',') {
                    state = EXPECT_KEY_OR_END;
                } else if (c == '}') {
                    if (!stack.empty()) {
                        stack.pop_back();
                    }
                    state = EXPECT_COMMA_OR_END;
                }
                break;
        }
    }
};

// macro defined in pybind11.h (common.h)
PYBIND11_MODULE(_core, m) {
    m.doc() = "C++ streaming JSON parser with Python bindings";

    // Expose the StreamJsonParser class along with its
    // constructor and two functions. 
    // Note that we use getPython for get to return a py::object
    py::class_<StreamingJsonParser>(m, "StreamingJsonParser")
        .def(py::init<bool>(), py::arg("strict_mode") = false)
        .def("consume", &StreamingJsonParser::consume)
        .def("get", &StreamingJsonParser::getPython);
            
    // Expose extra function for parsing without explictly creating obj. 
    m.def("parse_json", [](const std::string& json_str, bool strict_mode = false) {
            StreamingJsonParser parser(strict_mode);
            parser.consume(json_str);
            return parser.getPython();
        }, py::arg("json_str"), py::arg("strict_mode") = false);
}
