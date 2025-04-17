/**
 * StreamingJsonParser: A C++ implementation of a streaming JSON parser.
 */

#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
#include <memory>
#include <stdexcept>
#include <cassert>

// Forward declarations
class JsonValue;
class JsonString;
class JsonObject;

/**
 * Base class for JSON values
 */
class JsonValue {
public:
    virtual ~JsonValue() = default;
    virtual bool isString() const = 0;
    virtual bool isObject() const = 0;
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
    
    // Get all members
    const std::unordered_map<std::string, std::unique_ptr<JsonValue>>& getMembers() const {
        return members;
    }
    
private:
    std::unordered_map<std::string, std::unique_ptr<JsonValue>> members;
};

/**
 * Stack-based state machine parser for streaming JSON.
 * 
 * Assumptions (same as Python version):
 * 1) In one object no two keys are the same
 * 2) Expect one JSON object in stream
 * 3) Partial values like '{"foo":}' yield {} because value type is unknown
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
    
    // Constructor
    StreamingJsonParser(bool strict_mode = false) 
        : state(START), strict_mode(strict_mode), result(new JsonObject()) {
        // Initialize the expected characters for each state
        expected_chars[START] = "{";
        expected_chars[EXPECT_KEY_OR_END] = "\"}";
        expected_chars[EXPECT_COLON] = ":";
        expected_chars[EXPECT_VALUE] = "\"{";
        expected_chars[EXPECT_COMMA_OR_END] = ",}";
    }
    
    // Destructor
    ~StreamingJsonParser() = default;
    
    // Consume a string buffer
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
    
    // Get the parsed result
    JsonObject* get() const {
        return dynamic_cast<JsonObject*>(result.get());
    }
    
private:
    std::unique_ptr<JsonValue> result;
    std::vector<JsonObject*> stack;
    State state;
    std::string current_key;
    bool strict_mode;
    std::unordered_map<State, std::string> expected_chars;
    
    // Check if a character is whitespace
    bool isWhitespace(char c) const {
        return c == ' ' || c == '\n' || c == '\t' || c == '\r';
    }
    
    // Process a single character
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

/**
 * Helper functions for testing
 */

// Compare two JSON objects for equality
bool areEqual(const JsonObject* a, const JsonObject* b) {
    const auto& aMembers = a->getMembers();
    const auto& bMembers = b->getMembers();
    
    if (aMembers.size() != bMembers.size()) {
        return false;
    }
    
    for (const auto& [key, value] : aMembers) {
        if (!b->has(key)) {
            return false;
        }
        
        const auto* bValue = b->get(const_cast<std::string&>(key));
        
        if (value->isString() && bValue->isString()) {
            const auto* aString = dynamic_cast<const JsonString*>(value.get());
            const auto* bString = dynamic_cast<const JsonString*>(bValue);
            if (aString->getValue() != bString->getValue()) {
                return false;
            }
        } else if (value->isObject() && bValue->isObject()) {
            const auto* aObject = dynamic_cast<const JsonObject*>(value.get());
            const auto* bObject = dynamic_cast<const JsonObject*>(bValue);
            if (!areEqual(aObject, bObject)) {
                return false;
            }
        } else {
            return false;
        }
    }
    
    return true;
}

// Create a simple JSON object with string values
std::unique_ptr<JsonObject> createSimpleObject(
    std::initializer_list<std::pair<std::string, std::string>> items) {
    auto obj = std::make_unique<JsonObject>();
    for (const auto& [key, value] : items) {
        obj->set(key, std::make_unique<JsonString>(value));
    }
    return obj;
}

// Run tests similar to the Python version
void runTests() {
    // Test basic parsing
    auto test_streaming_json_parser = []() {
        StreamingJsonParser parser;
        parser.consume("{\"foo\": \n \"bar\"}asd");
        auto expected = createSimpleObject({{"foo", "bar"}});
        assert(areEqual(parser.get(), expected.get()));
        std::cout << "[v] test_streaming_json_parser" << std::endl;
    };
    
    // Test character-by-character parsing
    auto test_streaming_json_parser2 = []() {
        StreamingJsonParser parser;
        for (char c : "{\"foo\": \"bar\"}") {
            parser.consume(std::string(1, c));
        }
        auto expected = createSimpleObject({{"foo", "bar"}});
        assert(areEqual(parser.get(), expected.get()));
        std::cout << "[v] test_streaming_json_parser2" << std::endl;
    };
    
    // Test chunked parsing
    auto test_chunked_streaming_json_parser = []() {
        StreamingJsonParser parser;
        parser.consume("{\"foo\":");
        parser.consume("\"bar");
        auto expected = createSimpleObject({{"foo", "bar"}});
        assert(areEqual(parser.get(), expected.get()));
        std::cout << "[v] test_chunked_streaming_json_parser" << std::endl;
    };
    
    // Test empty object
    auto test_empty_object = []() {
        StreamingJsonParser parser;
        parser.consume("{}");
        auto expected = std::make_unique<JsonObject>();
        assert(areEqual(parser.get(), expected.get()));
        std::cout << "[v] test_empty_object" << std::endl;
    };
    
    // Test nested objects
    auto test_nested_objects = []() {
        StreamingJsonParser parser;
        parser.consume("{\"foo\": {\"bar\":\"lol\", \"bar2\":\"tr\"}}");
        
        auto inner = createSimpleObject({{"bar", "lol"}, {"bar2", "tr"}});
        auto expected = std::make_unique<JsonObject>();
        expected->set("foo", std::move(inner));
        
        assert(areEqual(parser.get(), expected.get()));
        std::cout << "[v] test_nested_objects" << std::endl;
    };
    
    // Run all tests
    test_streaming_json_parser();
    test_streaming_json_parser2();
    test_chunked_streaming_json_parser();
    test_empty_object();
    test_nested_objects();
}

int main() {
    runTests();
    return 0;
}
