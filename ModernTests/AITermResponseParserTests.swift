//
//  AITermResponseParserTests.swift
//  iTerm2
//
//  Tests for OpenAI-compatible chat completions response parsing,
//  including the modern tool_calls format and legacy function_call format.
//

import XCTest
@testable import iTerm2SharedARC

final class AITermResponseParserTests: XCTestCase {

    // MARK: - CompletionsMessage Decoding: Modern tool_calls Format

    func testCompletionsMessageDecodesModernToolCallsFormat() {
        let json = """
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_command_history",
                        "arguments": "{\"count\": 5}"
                    },
                    "id": "call_abc123"
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.role, .assistant)
        XCTAssertEqual(message.content, .string(""))
        XCTAssertNotNil(message.function_call)
        XCTAssertEqual(message.function_call?.name, "get_command_history")
        XCTAssertEqual(message.function_call?.arguments, "{\"count\": 5}")
        XCTAssertEqual(message.function_call?.id, "call_abc123")
        XCTAssertNotNil(message.tool_calls)
        XCTAssertEqual(message.tool_calls?.count, 1)
        XCTAssertEqual(message.tool_calls?.first?.function.name, "get_command_history")
        XCTAssertEqual(message.tool_calls?.first?.function.arguments, "{\"count\": 5}")
        XCTAssertEqual(message.tool_calls?.first?.id, "call_abc123")
    }

    func testCompletionsMessageDecodesMultipleToolCalls() {
        let json = """
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "func_a",
                        "arguments": "{\"a\": 1}"
                    },
                    "id": "call_1"
                },
                {
                    "type": "function",
                    "function": {
                        "name": "func_b",
                        "arguments": "{\"b\": 2}"
                    },
                    "id": "call_2"
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.tool_calls?.count, 2)
        // function_call should map to the first tool call
        XCTAssertEqual(message.function_call?.name, "func_a")
        XCTAssertEqual(message.function_call?.arguments, "{\"a\": 1}")
        XCTAssertEqual(message.function_call?.id, "call_1")
    }

    func testCompletionsMessageDecodesToolCallsWithComplexArguments() {
        let json = """
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "math",
                        "arguments": "{\"a\":123,\"b\":456}"
                    },
                    "id": "fQUmUBUZKuDqM7YyUFygQ60L5A6cKyr0"
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.function_call?.name, "math")
        XCTAssertEqual(message.function_call?.arguments, "{\"a\":123,\"b\":456}")
    }

    // MARK: - CompletionsMessage Decoding: Legacy function_call Format

    func testCompletionsMessageDecodesLegacyFunctionCallFormat() {
        let json = """
        {
            "role": "assistant",
            "function_call": {
                "name": "get_command_history",
                "arguments": "{\"count\": 5}"
            }
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.role, .assistant)
        XCTAssertNil(message.tool_calls)
        XCTAssertNotNil(message.function_call)
        XCTAssertEqual(message.function_call?.name, "get_command_history")
        XCTAssertEqual(message.function_call?.arguments, "{\"count\": 5}")
        XCTAssertNil(message.function_call?.id)
    }

    func testCompletionsMessageDecodesEmptyContentString() {
        let json = """
        {
            "role": "assistant",
            "content": ""
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.role, .assistant)
        XCTAssertEqual(message.content, .string(""))
        XCTAssertEqual(message.coercedContentString, "")
    }

    func testCompletionsMessageDecodesTextContent() {
        let json = """
        {
            "role": "assistant",
            "content": "2 + 2 = 4"
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.role, .assistant)
        XCTAssertEqual(message.content, .string("2 + 2 = 4"))
        XCTAssertEqual(message.coercedContentString, "2 + 2 = 4")
    }

    func testCompletionsMessageDecodesNullContent() {
        let json = """
        {
            "role": "assistant",
            "content": null
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.role, .assistant)
        XCTAssertNil(message.content)
        XCTAssertEqual(message.coercedContentString, "")
    }

    func testCompletionsMessageDecodesMinimalAssistantMessage() {
        let json = """
        {
            "role": "assistant"
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.role, .assistant)
        XCTAssertNil(message.content)
        XCTAssertNil(message.function_call)
        XCTAssertNil(message.tool_calls)
    }

    // MARK: - CompletionsMessage: tool_calls Takes Priority Over Legacy function_call

    func testToolCallsTakesPriorityOverLegacyFunctionCall() {
        // When both tool_calls and function_call are present, tool_calls should win
        let json = """
        {
            "role": "assistant",
            "function_call": {
                "name": "old_function",
                "arguments": "{}"
            },
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "new_function",
                        "arguments": "{\"a\": 1}"
                    },
                    "id": "call_new"
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        // tool_calls should take priority
        XCTAssertEqual(message.function_call?.name, "new_function")
        XCTAssertEqual(message.function_call?.arguments, "{\"a\": 1}")
        XCTAssertEqual(message.function_call?.id, "call_new")
        XCTAssertEqual(message.tool_calls?.count, 1)
        XCTAssertEqual(message.tool_calls?.first?.function.name, "new_function")
    }

    // MARK: - CompletionsMessage: llmMessage Conversion

    func testCompletionsMessageToLLMMessageWithToolCalls() {
        let json = """
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_command_history",
                        "arguments": "{\"count\": 5}"
                    },
                    "id": "call_abc123"
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)
        let llmMessage = message.llmMessage

        XCTAssertEqual(llmMessage.role, .assistant)
        switch llmMessage.body {
        case .functionCall(let call, let id):
            XCTAssertEqual(call.name, "get_command_history")
            XCTAssertEqual(call.arguments, "{\"count\": 5}")
            XCTAssertEqual(call.id, "call_abc123")
        default:
            XCTFail("Expected .functionCall body")
        }
    }

    func testCompletionsMessageToLLMMessageWithTextContent() {
        let json = """
        {
            "role": "assistant",
            "content": "Hello, how can I help?"
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)
        let llmMessage = message.llmMessage

        XCTAssertEqual(llmMessage.role, .assistant)
        switch llmMessage.body {
        case .text(let text):
            XCTAssertEqual(text, "Hello, how can I help?")
        default:
            XCTFail("Expected .text body")
        }
    }

    func testCompletionsMessageToLLMMessageWithFunctionOutput() {
        let json = """
        {
            "role": "assistant",
            "name": "get_command_history",
            "content": "ls -la\\ncd /tmp\\n"
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)
        let llmMessage = message.llmMessage

        XCTAssertEqual(llmMessage.role, .assistant)
        switch llmMessage.body {
        case .functionOutput(let name, let output, _):
            XCTAssertEqual(name, "get_command_history")
            XCTAssertEqual(output, "ls -la\\ncd /tmp\\n")
        default:
            XCTFail("Expected .functionOutput body")
        }
    }

    // MARK: - CompletionsMessage: Encoding Round-trip

    func testCompletionsMessageEncodeDecodeRoundTripWithToolCalls() {
        let json = """
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "math",
                        "arguments": "{\"a\":123,\"b\":456}"
                    },
                    "id": "call_xyz"
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        let original = try! JSONDecoder().decode(CompletionsMessage.self, from: data)
        let encoded = try! JSONEncoder().encode(original)
        let decoded = try! JSONDecoder().decode(CompletionsMessage.self, from: encoded)

        XCTAssertEqual(decoded.role, original.role)
        XCTAssertEqual(decoded.function_call?.name, original.function_call?.name)
        XCTAssertEqual(decoded.function_call?.arguments, original.function_call?.arguments)
        XCTAssertEqual(decoded.tool_calls?.count, original.tool_calls?.count)
    }

    func testCompletionsMessageEncodeDecodeRoundTripWithText() {
        let json = """
        {
            "role": "assistant",
            "content": "Hello world"
        }
        """
        let data = json.data(using: .utf8)!
        let original = try! JSONDecoder().decode(CompletionsMessage.self, from: data)
        let encoded = try! JSONEncoder().encode(original)
        let decoded = try! JSONDecoder().decode(CompletionsMessage.self, from: encoded)

        XCTAssertEqual(decoded.role, original.role)
        XCTAssertEqual(decoded.content, original.content)
    }

    // MARK: - CompletionsMessage: Content Array

    func testCompletionsMessageDecodesContentArray() {
        let json = """
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Here is the answer"},
                {"type": "text", "text": " with more details"}
            ]
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        switch message.content {
        case .array(let parts):
            XCTAssertEqual(parts.count, 2)
            if case .text(let tc) = parts[0] {
                XCTAssertEqual(tc.text, "Here is the answer")
            } else {
                XCTFail("Expected text content part")
            }
            if case .text(let tc) = parts[1] {
                XCTAssertEqual(tc.text, " with more details")
            } else {
                XCTFail("Expected text content part")
            }
        default:
            XCTFail("Expected .array content")
        }
    }

    // MARK: - LLMModernResponseParser: Non-streaming

    func testModernResponseParserParsesToolCallsResponse() {
        let json = """
        {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "Qwen3.6-35B-A3B",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "type": "function",
                                "function": {
                                    "name": "get_command_history",
                                    "arguments": "{\"count\": 5}"
                                },
                                "id": "call_abc123"
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ],
            "usage": {
                "prompt_tokens": 277,
                "completion_tokens": 135,
                "total_tokens": 412
            }
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        let messages = response!.choiceMessages
        XCTAssertEqual(messages.count, 1)
        XCTAssertEqual(messages[0].role, .assistant)
        switch messages[0].body {
        case .functionCall(let call, _):
            XCTAssertEqual(call.name, "get_command_history")
            XCTAssertEqual(call.arguments, "{\"count\": 5}")
            XCTAssertEqual(call.id, "call_abc123")
        default:
            XCTFail("Expected .functionCall body, got \(messages[0].body)")
        }
    }

    func testModernResponseParserParsesTextResponse() {
        let json = """
        {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "Qwen3.6-35B-A3B",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "2 + 2 = 4"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        let messages = response!.choiceMessages
        XCTAssertEqual(messages.count, 1)
        switch messages[0].body {
        case .text(let text):
            XCTAssertEqual(text, "2 + 2 = 4")
        default:
            XCTFail("Expected .text body")
        }
    }

    func testModernResponseParserParsesLegacyFunctionCallResponse() {
        let json = """
        {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "test",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "function_call": {
                            "name": "old_function",
                            "arguments": "{}"
                        }
                    },
                    "finish_reason": "function_call"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        let messages = response!.choiceMessages
        XCTAssertEqual(messages.count, 1)
        switch messages[0].body {
        case .functionCall(let call, _):
            XCTAssertEqual(call.name, "old_function")
            XCTAssertEqual(call.arguments, "{}")
        default:
            XCTFail("Expected .functionCall body")
        }
    }

    // MARK: - LLMModernStreamingResponseParser: Streaming Chunks

    func testStreamingParserParsesTextDeltaChunk() {
        let json = """
        {
            "id": "chatcmpl-stream",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "Qwen3.6-35B-A3B",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": null
                },
                {
                    "index": 0,
                    "delta": {"content": "Hello"},
                    "finish_reason": null
                },
                {
                    "index": 0,
                    "delta": {"content": " world"},
                    "finish_reason": null
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernStreamingResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        let messages = response!.choiceMessages
        XCTAssertEqual(messages.count, 1)
        switch messages[0].body {
        case .text(let text):
            XCTAssertEqual(text, "Hello world")
        default:
            XCTFail("Expected .text body, got \(messages[0].body)")
        }
    }

    func testStreamingParserParsesToolCallsDeltaChunks() {
        let json = """
        {
            "id": "chatcmpl-stream",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "Qwen3.6-35B-A3B",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": null
                },
                {
                    "index": 0,
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "type": "function",
                                "function": {"name": "get", "arguments": ""},
                                "id": "call_"
                            }
                        ]
                    },
                    "finish_reason": null
                },
                {
                    "index": 0,
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "type": "function",
                                "function": {"arguments": "{\"count\":"},
                                "id": "call_"
                            }
                        ]
                    },
                    "finish_reason": null
                },
                {
                    "index": 0,
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "type": "function",
                                "function": {"arguments": " 5}\""},
                                "id": "call_abc123"
                            }
                        ]
                    },
                    "finish_reason": null
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernStreamingResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        let messages = response!.choiceMessages
        XCTAssertEqual(messages.count, 1)
        switch messages[0].body {
        case .functionCall(let call, _):
            XCTAssertEqual(call.name, "get_command_history")
            XCTAssertEqual(call.arguments, "{\"count\": 5}")
        default:
            XCTFail("Expected .functionCall body, got \(messages[0].body)")
        }
    }

    // MARK: - Streaming Parser: Final Chunk Skipping

    func testStreamingParserSkipsFinalChunkWithFinishReasonToolCalls() {
        // When finish_reason is "tool_calls" with empty delta, it should be skipped
        let json = """
        {
            "id": "chatcmpl-stream",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "Qwen3.6-35B-A3B",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": null
                },
                {
                    "index": 0,
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "type": "function",
                                "function": {"name": "math", "arguments": "{\"a\":1,\"b\":2}"},
                                "id": "call_xyz"
                            }
                        ]
                    },
                    "finish_reason": null
                },
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "tool_calls"
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernStreamingResponseParser()
        let response = try! parser.parse(data: data)

        let messages = response!.choiceMessages
        // The final chunk with finish_reason="tool_calls" and empty delta should be skipped
        XCTAssertEqual(messages.count, 1)
        switch messages[0].body {
        case .functionCall(let call, _):
            XCTAssertEqual(call.name, "math")
            XCTAssertEqual(call.arguments, "{\"a\":1,\"b\":2}")
        default:
            XCTFail("Expected .functionCall body")
        }
    }

    func testStreamingParserSkipsFinalChunkWithFinishReasonFunctionCall() {
        // Legacy: when finish_reason is "function_call" with empty delta, it should be skipped
        let json = """
        {
            "id": "chatcmpl-stream",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "test",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": null
                },
                {
                    "index": 0,
                    "delta": {"function_call": {"name": "old_fn", "arguments": "{}"}},
                    "finish_reason": null
                },
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "function_call"
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernStreamingResponseParser()
        let response = try! parser.parse(data: data)

        let messages = response!.choiceMessages
        XCTAssertEqual(messages.count, 1)
        switch messages[0].body {
        case .functionCall(let call, _):
            XCTAssertEqual(call.name, "old_fn")
            XCTAssertEqual(call.arguments, "{}")
        default:
            XCTFail("Expected .functionCall body")
        }
    }

    func testStreamingParserDoesNotSkipChunkWithToolCallDataAndFinishReason() {
        // If the final chunk still has tool call data, it should NOT be skipped
        let json = """
        {
            "id": "chatcmpl-stream",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "Qwen3.6-35B-A3B",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": null
                },
                {
                    "index": 0,
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "type": "function",
                                "function": {"name": "math", "arguments": "{}"},
                                "id": "call_1"
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernStreamingResponseParser()
        let response = try! parser.parse(data: data)

        let messages = response!.choiceMessages
        // The chunk has tool_calls data, so it should NOT be skipped
        XCTAssertEqual(messages.count, 1)
        switch messages[0].body {
        case .functionCall(let call, _):
            XCTAssertEqual(call.name, "math")
        default:
            XCTFail("Expected .functionCall body")
        }
    }

    // MARK: - LLMModernStreamingResponseParser: SSE Event Splitting

    func testStreamingParserSplitsSSEEvents() {
        let sse = """
        event: message
        data: {"id":"1","choices":[{"index":0,"delta":{"content":"a"}}]}

        event: message
        data: {"id":"2","choices":[{"index":0,"delta":{"content":"b"}}]}

        """
        let (json, remainder) = LLMModernStreamingResponseParser().splitFirstJSONEvent(from: sse)
        XCTAssertNotNil(json)
        XCTAssertTrue(remainder.contains("\"id\":\"2\""))
    }

    // MARK: - CompletionsMessage: Equatable

    func testCompletionsMessageEquatableWithSameText() {
        let json1 = """
        {"role": "assistant", "content": "hello"}
        """
        let json2 = """
        {"role": "assistant", "content": "hello"}
        """
        let data1 = json1.data(using: .utf8)!
        let data2 = json2.data(using: .utf8)!
        let msg1 = try! JSONDecoder().decode(CompletionsMessage.self, from: data1)
        let msg2 = try! JSONDecoder().decode(CompletionsMessage.self, from: data2)

        XCTAssertEqual(msg1, msg2)
    }

    func testCompletionsMessageEquatableWithDifferentText() {
        let json1 = """
        {"role": "assistant", "content": "hello"}
        """
        let json2 = """
        {"role": "assistant", "content": "world"}
        """
        let data1 = json1.data(using: .utf8)!
        let data2 = json2.data(using: .utf8)!
        let msg1 = try! JSONDecoder().decode(CompletionsMessage.self, from: data1)
        let msg2 = try! JSONDecoder().decode(CompletionsMessage.self, from: data2)

        XCTAssertNotEqual(msg1, msg2)
    }

    func testCompletionsMessageEquatableWithSameToolCalls() {
        let json1 = """
        {"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": "f", "arguments": "{}"}, "id": "c1"}]}
        """
        let json2 = """
        {"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": "f", "arguments": "{}"}, "id": "c1"}]}
        """
        let data1 = json1.data(using: .utf8)!
        let data2 = json2.data(using: .utf8)!
        let msg1 = try! JSONDecoder().decode(CompletionsMessage.self, from: data1)
        let msg2 = try! JSONDecoder().decode(CompletionsMessage.self, from: data2)

        XCTAssertEqual(msg1, msg2)
    }

    // MARK: - CompletionsMessage: LLM.Message Initialization

    func testCompletionsMessageInitFromLLMMessageWithText() {
        let llmMsg = LLM.Message(role: .assistant, content: "Hello", name: nil, function_call: nil)
        let compMsg = CompletionsMessage(llmMsg)

        XCTAssertNotNil(compMsg)
        XCTAssertEqual(compMsg?.role, .assistant)
        XCTAssertEqual(compMsg?.content, .string("Hello"))
    }

    func testCompletionsMessageInitFromLLMMessageWithFunctionCall() {
        let funcCall = LLM.FunctionCall(name: "my_func", arguments: "{\"x\": 1}", id: "call_1")
        let llmMsg = LLM.Message(role: .assistant, function_call: funcCall)
        let compMsg = CompletionsMessage(llmMsg)

        XCTAssertNotNil(compMsg)
        XCTAssertEqual(compMsg?.function_call?.name, "my_func")
        XCTAssertEqual(compMsg?.function_call?.arguments, "{\"x\": 1}")
    }

    func testCompletionsMessageInitFromLLMMessageWithFunctionOutput() {
        let llmMsg = LLM.Message(role: .assistant, content: "result", name: "my_func", function_call: nil)
        let compMsg = CompletionsMessage(llmMsg)

        XCTAssertNotNil(compMsg)
        XCTAssertEqual(compMsg?.functionName, "my_func")
        XCTAssertEqual(compMsg?.content, .string("result"))
    }

    func testCompletionsMessageInitFromLLMMessageUninitialized() {
        let llmMsg = LLM.Message(role: .assistant, body: .uninitialized)
        let compMsg = CompletionsMessage(llmMsg)

        XCTAssertNil(compMsg)
    }

    // MARK: - Edge Cases

    func testCompletionsMessageDecodesEmptyToolCallsArray() {
        let json = """
        {
            "role": "assistant",
            "content": "no tools needed",
            "tool_calls": []
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.role, .assistant)
        XCTAssertEqual(message.content, .string("no tools needed"))
        XCTAssertEqual(message.tool_calls?.count, 0)
        XCTAssertNil(message.function_call)
    }

    func testCompletionsMessageDecodesToolCallWithMissingOptionalFields() {
        let json = """
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "function": {
                        "name": "simple_func",
                        "arguments": "{}"
                    }
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.tool_calls?.first?.type, nil)
        XCTAssertEqual(message.tool_calls?.first?.function.name, "simple_func")
        XCTAssertNil(message.tool_calls?.first?.id)
    }

    func testCompletionsMessageDecodesToolCallWithEmptyArguments() {
        let json = """
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "no_args_func",
                        "arguments": ""
                    },
                    "id": "call_empty"
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.function_call?.arguments, "")
    }

    // MARK: - CompletionsMessage: Encoding Produces Valid JSON

    func testCompletionsMessageEncodeProducesValidToolCallsJSON() {
        let json = """
        {"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": "get_command_history", "arguments": "{\"count\": 5}"}, "id": "call_abc123"}]}
        """
        let data = json.data(using: .utf8)!
        let original = try! JSONDecoder().decode(CompletionsMessage.self, from: data)
        let encoded = try! JSONEncoder().encode(original)
        let encodedString = String(data: encoded, encoding: .utf8)!

        // Verify the encoded JSON contains the expected keys
        XCTAssertTrue(encodedString.contains("\"tool_calls\""))
        XCTAssertTrue(encodedString.contains("\"function\""))
        XCTAssertTrue(encodedString.contains("\"get_command_history\""))
        XCTAssertTrue(encodedString.contains("\"call_abc123\""))
    }

    func testCompletionsMessageEncodeProducesValidTextJSON() {
        let json = """
        {"role": "assistant", "content": "Hello world"}
        """
        let data = json.data(using: .utf8)!
        let original = try! JSONDecoder().decode(CompletionsMessage.self, from: data)
        let encoded = try! JSONEncoder().encode(original)
        let encodedString = String(data: encoded, encoding: .utf8)!

        XCTAssertTrue(encodedString.contains("\"content\""))
        XCTAssertTrue(encodedString.contains("\"Hello world\""))
    }

    // MARK: - CompletionsMessage: Coerced Content String

    func testCoercedContentStringReturnsEmptyForNilContent() {
        let json = """
        {"role": "assistant"}
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.coercedContentString, "")
    }

    func testCoercedContentStringReturnsStringContent() {
        let json = """
        {"role": "assistant", "content": "Hello world"}
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.coercedContentString, "Hello world")
    }

    func testCoercedContentStringJoinsArrayContent() {
        let json = """
        {"role": "assistant", "content": [{"type": "text", "text": "Hello"}, {"type": "text", "text": " world"}]}
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.coercedContentString, "Hello\n world")
    }

    // MARK: - CompletionsMessage: Approximate Token Count

    func testApproximateTokenCountForStringContent() {
        let json = """
        {"role": "assistant", "content": "hello"}
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        // "hello" = 5 chars / 2 = 2 tokens + 1 base = 3
        XCTAssertGreaterThan(message.approximateTokenCount, 0)
    }

    func testApproximateTokenCountForNilContent() {
        let json = """
        {"role": "assistant"}
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.approximateTokenCount, 0)
    }

    // MARK: - LLMModernResponseParser: Edge Cases

    func testModernResponseParserHandlesEmptyChoices() {
        let json = """
        {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "test",
            "choices": [],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 0,
                "total_tokens": 10
            }
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        XCTAssertTrue(response!.choiceMessages.isEmpty)
    }

    func testModernResponseParserHandlesMultipleChoices() {
        let json = """
        {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "test",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "First"},
                    "finish_reason": "stop"
                },
                {
                    "index": 1,
                    "message": {"role": "assistant", "content": "Second"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        XCTAssertEqual(response!.choiceMessages.count, 2)
        switch response!.choiceMessages[0].body {
        case .text(let text): XCTAssertEqual(text, "First")
        default: XCTFail("Expected .text body")
        }
        switch response!.choiceMessages[1].body {
        case .text(let text): XCTAssertEqual(text, "Second")
        default: XCTFail("Expected .text body")
        }
    }

    func testModernResponseParserPreservesResponseMetadata() {
        let json = """
        {
            "id": "chatcmpl-abc123",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "gpt-4o",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "test"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 5,
                "total_tokens": 25
            }
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernResponseParser()
        let response = try! parser.parse(data: data) as! LLMModernResponseParser.ModernResponse

        XCTAssertEqual(response.id, "chatcmpl-abc123")
        XCTAssertEqual(response.object, "chat.completion")
        XCTAssertEqual(response.created, 1700000000)
        XCTAssertEqual(response.model, "gpt-4o")
        XCTAssertNotNil(response.usage)
        XCTAssertEqual(response.usage?.prompt_tokens, 20)
        XCTAssertEqual(response.usage?.completion_tokens, 5)
        XCTAssertEqual(response.usage?.total_tokens, 25)
    }

    // MARK: - LLMModernStreamingResponseParser: Edge Cases

    func testStreamingParserHandlesEmptyChoices() {
        let json = """
        {
            "id": "chatcmpl-stream",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "test",
            "choices": []
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernStreamingResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        XCTAssertTrue(response!.choiceMessages.isEmpty)
    }

    func testStreamingParserHandlesMultipleChoices() {
        let json = """
        {
            "id": "chatcmpl-stream",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "test",
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": "First choice"},
                    "finish_reason": null
                },
                {
                    "index": 1,
                    "delta": {"content": "Second choice"},
                    "finish_reason": null
                }
            ]
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernStreamingResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        XCTAssertEqual(response!.choiceMessages.count, 2)
    }

    func testStreamingParserAccumulatesTextAcrossChunks() {
        // Each chunk contributes a piece of text, they should accumulate
        let json = """
        {
            "id": "chatcmpl-stream",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "test",
            "choices": [
                {"index": 0, "delta": {"content": "Hello"}, "finish_reason": null},
                {"index": 0, "delta": {"content": " "}, "finish_reason": null},
                {"index": 0, "delta": {"content": "World"}, "finish_reason": null},
                {"index": 0, "delta": {}, "finish_reason": "stop"}
            ]
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernStreamingResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        let messages = response!.choiceMessages
        XCTAssertEqual(messages.count, 1)
        switch messages[0].body {
        case .text(let text): XCTAssertEqual(text, "Hello World")
        default: XCTFail("Expected .text body, got \(messages[0].body)")
        }
    }

    func testStreamingParserAccumulatesToolCallNameAcrossChunks() {
        // Function name can arrive in pieces across chunks
        let json = """
        {
            "id": "chatcmpl-stream",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "test",
            "choices": [
                {"index": 0, "delta": {"role": "assistant"}, "finish_reason": null},
                {"index": 0, "delta": {"tool_calls": [{"index": 0, "type": "function", "function": {"name": "get_"}}, "id": "call_1"]}], "finish_reason": null},
                {"index": 0, "delta": {"tool_calls": [{"index": 0, "function": {"name": "command_history"}}, "id": "call_1"]}], "finish_reason": null},
                {"index": 0, "delta": {"tool_calls": [{"index": 0, "function": {"arguments": "{}"}}, "id": "call_1"]}], "finish_reason": null},
                {"index": 0, "delta": {}, "finish_reason": "tool_calls"}
            ]
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernStreamingResponseParser()
        let response = try! parser.parse(data: data)

        XCTAssertNotNil(response)
        let messages = response!.choiceMessages
        XCTAssertEqual(messages.count, 1)
        switch messages[0].body {
        case .functionCall(let call, _):
            // The parser accumulates the name from chunks
            XCTAssertTrue(call.name.contains("get"))
        default:
            XCTFail("Expected .functionCall body, got \(messages[0].body)")
        }
    }

    func testStreamingParserSkipsFinishReasonStopChunk() {
        // Final chunk with finish_reason="stop" and empty delta should be skipped
        let json = """
        {
            "id": "chatcmpl-stream",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "test",
            "choices": [
                {"index": 0, "delta": {"content": "Hello"}, "finish_reason": null},
                {"index": 0, "delta": {}, "finish_reason": "stop"}
            ]
        }
        """
        let data = json.data(using: .utf8)!
        var parser = LLMModernStreamingResponseParser()
        let response = try! parser.parse(data: data)

        let messages = response!.choiceMessages
        XCTAssertEqual(messages.count, 1)
        switch messages[0].body {
        case .text(let text): XCTAssertEqual(text, "Hello")
        default: XCTFail("Expected .text body")
        }
    }

    // MARK: - SplitServerSentEvents

    func testSplitFirstJSONEventHandlesEmptyString() {
        let (json, remainder) = LLMModernStreamingResponseParser().splitFirstJSONEvent(from: "")
        XCTAssertNil(json)
        XCTAssertTrue(remainder.isEmpty)
    }

    func testSplitFirstJSONEventHandlesJSONWithoutSSE() {
        let rawJSON = """
        {"id":"1","choices":[{"index":0,"delta":{"content":"a"}}]}
        """
        let (json, remainder) = LLMModernStreamingResponseParser().splitFirstJSONEvent(from: rawJSON)
        XCTAssertNotNil(json)
        XCTAssertTrue(remainder.isEmpty)
    }

    func testSplitFirstJSONEventHandlesMultipleSSEEvents() {
        let sse = """
        event: message
        data: {"id":"1","choices":[{"index":0,"delta":{"content":"a"}}]}

        event: message
        data: {"id":"2","choices":[{"index":0,"delta":{"content":"b"}}]}

        event: done
        data: [DONE]

        """
        let parser = LLMModernStreamingResponseParser()

        // First event
        let (json1, remainder1) = parser.splitFirstJSONEvent(from: sse)
        XCTAssertNotNil(json1)
        XCTAssertTrue(remainder1.contains("\"id\":\"2\""))
        XCTAssertTrue(remainder1.contains("[DONE]"))

        // Second event
        let (json2, remainder2) = parser.splitFirstJSONEvent(from: remainder1)
        XCTAssertNotNil(json2)
        XCTAssertTrue(remainder2.contains("[DONE]"))

        // Third event (DONE)
        let (json3, remainder3) = parser.splitFirstJSONEvent(from: remainder2)
        XCTAssertNotNil(json3)
        XCTAssertTrue(remainder3.isEmpty || remainder3.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
    }

    // MARK: - CompletionsMessage: Role Handling

    func testCompletionsMessageDecodesUserMessage() {
        let json = """
        {"role": "user", "content": "What is 2+2?"}
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.role, .user)
        XCTAssertEqual(message.coercedContentString, "What is 2+2?")
    }

    func testCompletionsMessageDecodesSystemMessage() {
        let json = """
        {"role": "system", "content": "You are a helpful assistant."}
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.role, .system)
        XCTAssertEqual(message.coercedContentString, "You are a helpful assistant.")
    }

    func testCompletionsMessageDecodesToolMessage() {
        let json = """
        {"role": "tool", "content": "result here", "tool_call_id": "call_123"}
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)

        XCTAssertEqual(message.role, .tool)
        XCTAssertEqual(message.coercedContentString, "result here")
    }

    // MARK: - CompletionsMessage: LLM.Message Conversion Edge Cases

    func testCompletionsMessageToLLMMessageWithEmptyToolCall() {
        let json = """
        {"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": "empty", "arguments": ""}, "id": "call_empty"}]}
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)
        let llmMessage = message.llmMessage

        XCTAssertEqual(llmMessage.role, .assistant)
        switch llmMessage.body {
        case .functionCall(let call, _):
            XCTAssertEqual(call.name, "empty")
            XCTAssertEqual(call.arguments, "")
        default:
            XCTFail("Expected .functionCall body")
        }
    }

    func testCompletionsMessageToLLMMessageWithUninitializedBody() {
        let json = """
        {"role": "assistant"}
        """
        let data = json.data(using: .utf8)!
        let message = try! JSONDecoder().decode(CompletionsMessage.self, from: data)
        let llmMessage = message.llmMessage

        XCTAssertEqual(llmMessage.role, .assistant)
        switch llmMessage.body {
        case .uninitialized:
            break // Expected
        default:
            XCTFail("Expected .uninitialized body")
        }
    }

    // MARK: - CompletionsMessage: Content Part Token Count

    func testContentPartTokenCountForText() {
        let json = """
        {"content": [{"type": "text", "text": "hello world"}]}
        """
        let data = json.data(using: .utf8)!
        let content = try! JSONDecoder().decode(CompletionsMessage.Content.self, from: data)

        switch content {
        case .array(let parts):
            let totalTokens = parts.map { $0.approximateTokenCount }.reduce(0, +)
            XCTAssertGreaterThan(totalTokens, 0)
        default:
            XCTFail("Expected .array content")
        }
    }

    // MARK: - ModernStreamingResponse: Properties

    func testModernStreamingResponseIsStreamingResponse() {
        let json = """
        {"id":"1","object":"chat.completion.chunk","created":1234567890,"model":"test","choices":[]}
        """
        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let response = try! decoder.decode(LLMModernStreamingResponseParser.ModernStreamingResponse.self, from: data)

        XCTAssertTrue(response.isStreamingResponse)
        XCTAssertNil(response.newlyCreatedResponseID)
        XCTAssertFalse(response.ignore)
    }
}
