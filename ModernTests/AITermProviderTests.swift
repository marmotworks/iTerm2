//
//  AITermProviderTests.swift
//  iTerm2
//
//  Tests for LLMProvider properties including functionsSupported API detection,
//  displayName, dynamicModelsSupported, responseParser selection, and MIMETypeIsTextual.
//

import XCTest
@testable import iTerm2SharedARC

final class AITermProviderTests: XCTestCase {

    // MARK: - LLMProvider.functionsSupported: Ollama Native API

    func testFunctionsSupportedReturnsFalseForOllamaNativeAPIWithStreaming() {
        // Ollama's native /api/chat endpoint requires stream=false for function calling
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "llama3.3:latest",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://localhost:11434/api/chat",
            api: .llama,
            features: features,
            vendor: .llama
        )
        let provider = LLMProvider(model: model)

        // Streaming is enabled via features, so functionsSupported should be false
        XCTAssertFalse(provider.functionsSupported)
    }

    func testFunctionsSupportedReturnsFalseForOllamaGenerateAPIWithStreaming() {
        // Ollama's native /api/generate endpoint also has the same limitation
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "llama3:latest",
            contextWindowTokens: 8192,
            maxResponseTokens: 8192,
            url: "http://localhost:11434/api/generate",
            api: .llama,
            features: features,
            vendor: .llama
        )
        let provider = LLMProvider(model: model)

        XCTAssertFalse(provider.functionsSupported)
    }

    func testFunctionsSupportedReturnsTrueForOllamaNativeAPIWithoutStreaming() {
        // When streaming is NOT enabled, function calling should work with Ollama native API
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling]
        features.remove(.streaming)
        let model = AIMetadata.Model(
            name: "llama3.3:latest",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://localhost:11434/api/chat",
            api: .llama,
            features: features,
            vendor: .llama
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.functionsSupported)
    }

    // MARK: - LLMProvider.functionsSupported: llama-server OpenAI-Compatible API

    func testFunctionsSupportedReturnsTrueForLlamaServerOpenAIEndpointWithStreaming() {
        // llama-server's /v1/chat/completions (OpenAI-compatible) supports both streaming and function calling
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "llama3.3:latest",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://localhost:8001/v1/chat/completions",
            api: .chatCompletions,
            features: features,
            vendor: .llama
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.functionsSupported)
    }

    func testFunctionsSupportedReturnsTrueForLlamaServerWithChatCompletionsAPI() {
        // Model name contains "llama" but URL points to OpenAI-compatible endpoint
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "llama3.1:8b",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://127.0.0.1:8080/v1/chat/completions",
            api: .chatCompletions,
            features: features,
            vendor: nil
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.functionsSupported)
    }

    func testFunctionsSupportedReturnsTrueForLlamaServerOpenAIAPI() {
        // OpenAI's own endpoint should work with function calling
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: features,
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.functionsSupported)
    }

    // MARK: - LLMProvider.functionsSupported: Non-llama Models

    func testFunctionsSupportedForGeminiModel() {
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "gemini-2.0-flash",
            contextWindowTokens: 1_048_576,
            maxResponseTokens: 8_192,
            url: "https://generativelanguage.googleapis.com/v1beta/models/{{MODEL}}",
            api: .gemini,
            features: features,
            vendor: .gemini
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.functionsSupported)
    }

    func testFunctionsSupportedForAnthropicModel() {
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "claude-sonnet-4-5",
            contextWindowTokens: 200_000,
            maxResponseTokens: 64_000,
            url: "https://api.anthropic.com/v1/messages",
            api: .anthropic,
            features: features,
            vendor: .anthropic
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.functionsSupported)
    }

    func testFunctionsSupportedForDeepSeekModel() {
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "deepseek-chat",
            contextWindowTokens: 128_000,
            maxResponseTokens: 8_000,
            url: "https://api.deepseek.com/v1/chat/completions",
            api: .deepSeek,
            features: features,
            vendor: .deepSeek
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.functionsSupported)
    }

    func testFunctionsSupportedReturnsFalseWhenFeatureDisabled() {
        // When functionCalling feature is not set, should return false
        var features: Set<AIMetadata.Model.Feature> = [.streaming]
        features.remove(.functionCalling)
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: features,
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertFalse(provider.functionsSupported)
    }

    // MARK: - LLMProvider.displayName

    func testDisplayNameReturnsOpenAIForOpenAIHost() {
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertEqual(provider.displayName, "OpenAI")
    }

    func testDisplayNameReturnsGoogleForGeminiHost() {
        let model = AIMetadata.Model(
            name: "gemini-2.0-flash",
            contextWindowTokens: 1_048_576,
            maxResponseTokens: 8_192,
            url: "https://generativelanguage.googleapis.com/v1beta/models/{{MODEL}}",
            api: .gemini,
            features: [.functionCalling, .streaming],
            vendor: .gemini
        )
        let provider = LLMProvider(model: model)

        XCTAssertEqual(provider.displayName, "Google")
    }

    func testDisplayNameReturnsAzureForAzureHost() {
        let model = AIMetadata.Model(
            name: "gpt-4",
            contextWindowTokens: 8192,
            maxResponseTokens: 4096,
            url: "https://my-resource.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-02-01",
            api: .chatCompletions,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertEqual(provider.displayName, "Azure")
    }

    func testDisplayNameReturnsDeepSeekForDeepSeekHost() {
        let model = AIMetadata.Model(
            name: "deepseek-chat",
            contextWindowTokens: 128_000,
            maxResponseTokens: 8_000,
            url: "https://api.deepseek.com/v1/chat/completions",
            api: .deepSeek,
            features: [.functionCalling, .streaming],
            vendor: .deepSeek
        )
        let provider = LLMProvider(model: model)

        XCTAssertEqual(provider.displayName, "Deep Seek")
    }

    func testDisplayNameReturnsAnthropicForAnthropicHost() {
        let model = AIMetadata.Model(
            name: "claude-sonnet-4-5",
            contextWindowTokens: 200_000,
            maxResponseTokens: 64_000,
            url: "https://api.anthropic.com/v1/messages",
            api: .anthropic,
            features: [.functionCalling, .streaming],
            vendor: .anthropic
        )
        let provider = LLMProvider(model: model)

        XCTAssertEqual(provider.displayName, "Anthropic")
    }

    func testDisplayNameReturnsLlamaForLlamaModelName() {
        let model = AIMetadata.Model(
            name: "llama3.3:latest",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://localhost:11434/api/chat",
            api: .llama,
            features: [.streaming, .functionCalling],
            vendor: .llama
        )
        let provider = LLMProvider(model: model)

        XCTAssertEqual(provider.displayName, "Llama")
    }

    func testDisplayNameReturnsUnknownForUnrecognizedHost() {
        let model = AIMetadata.Model(
            name: "custom-model",
            contextWindowTokens: 8192,
            maxResponseTokens: 4096,
            url: "https://custom-api.example.com/v1/chat",
            api: .chatCompletions,
            features: [],
            vendor: nil
        )
        let provider = LLMProvider(model: model)

        XCTAssertEqual(provider.displayName, "Unknown Platform")
    }

    // MARK: - LLMProvider.dynamicModelsSupported

    func testDynamicModelsSupportedReturnsFalseForAzure() {
        let model = AIMetadata.Model(
            name: "gpt-4",
            contextWindowTokens: 8192,
            maxResponseTokens: 4096,
            url: "https://my-resource.openai.azure.com/openai/deployments/gpt-4",
            api: .chatCompletions,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertFalse(provider.dynamicModelsSupported)
    }

    func testDynamicModelsSupportedReturnsFalseForGemini() {
        let model = AIMetadata.Model(
            name: "gemini-2.0-flash",
            contextWindowTokens: 1_048_576,
            maxResponseTokens: 8_192,
            url: "https://generativelanguage.googleapis.com/v1beta/models/{{MODEL}}",
            api: .gemini,
            features: [.functionCalling, .streaming],
            vendor: .gemini
        )
        let provider = LLMProvider(model: model)

        XCTAssertFalse(provider.dynamicModelsSupported)
    }

    func testDynamicModelsSupportedReturnsTrueForOpenAI() {
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.dynamicModelsSupported)
    }

    func testDynamicModelsSupportedReturnsTrueForAnthropic() {
        let model = AIMetadata.Model(
            name: "claude-sonnet-4-5",
            contextWindowTokens: 200_000,
            maxResponseTokens: 64_000,
            url: "https://api.anthropic.com/v1/messages",
            api: .anthropic,
            features: [.functionCalling, .streaming],
            vendor: .anthropic
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.dynamicModelsSupported)
    }

    // MARK: - LLMProvider.responseParser

    func testResponseParserReturnsModernParserForChatCompletions() {
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        let parser = provider.responseParser()
        XCTAssertTrue(parser is LLMModernResponseParser)
    }

    func testResponseParserReturnsModernParserForEarlyO1() {
        let model = AIMetadata.Model(
            name: "o1",
            contextWindowTokens: 128_000,
            maxResponseTokens: 32_768,
            url: "https://api.openai.com/v1/chat/completions",
            api: .earlyO1,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        let parser = provider.responseParser()
        XCTAssertTrue(parser is LLMModernResponseParser)
    }

    func testResponseParserReturnsResponsesParser() {
        let model = AIMetadata.Model(
            name: "gpt-5",
            contextWindowTokens: 400_000,
            maxResponseTokens: 128_000,
            url: "https://api.openai.com/v1/responses",
            api: .responses,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        let parser = provider.responseParser()
        XCTAssertTrue(parser is ResponsesResponseParser)
    }

    func testResponseParserReturnsGeminiParser() {
        let model = AIMetadata.Model(
            name: "gemini-2.0-flash",
            contextWindowTokens: 1_048_576,
            maxResponseTokens: 8_192,
            url: "https://generativelanguage.googleapis.com/v1beta/models/{{MODEL}}",
            api: .gemini,
            features: [.functionCalling, .streaming],
            vendor: .gemini
        )
        let provider = LLMProvider(model: model)

        let parser = provider.responseParser()
        XCTAssertTrue(parser is LLMGeminiResponseParser)
    }

    func testResponseParserReturnsLlamaParser() {
        let model = AIMetadata.Model(
            name: "llama3.3:latest",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://localhost:11434/api/chat",
            api: .llama,
            features: [.streaming, .functionCalling],
            vendor: .llama
        )
        let provider = LLMProvider(model: model)

        let parser = provider.responseParser()
        XCTAssertTrue(parser is LlamaResponseParser)
    }

    func testResponseParserReturnsDeepSeekParser() {
        let model = AIMetadata.Model(
            name: "deepseek-chat",
            contextWindowTokens: 128_000,
            maxResponseTokens: 8_000,
            url: "https://api.deepseek.com/v1/chat/completions",
            api: .deepSeek,
            features: [.functionCalling, .streaming],
            vendor: .deepSeek
        )
        let provider = LLMProvider(model: model)

        let parser = provider.responseParser()
        XCTAssertTrue(parser is DeepSeekResponseParser)
    }

    func testResponseParserReturnsAnthropicParser() {
        let model = AIMetadata.Model(
            name: "claude-sonnet-4-5",
            contextWindowTokens: 200_000,
            maxResponseTokens: 64_000,
            url: "https://api.anthropic.com/v1/messages",
            api: .anthropic,
            features: [.functionCalling, .streaming],
            vendor: .anthropic
        )
        let provider = LLMProvider(model: model)

        let parser = provider.responseParser()
        XCTAssertTrue(parser is AnthropicResponseParser)
    }

    // MARK: - LLMProvider.streamingResponseParser

    func testStreamingResponseParserReturnsModernParserForChatCompletions() {
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        let parser = provider.streamingResponseParser(stream: true)
        XCTAssertTrue(parser is LLMModernStreamingResponseParser)
    }

    func testStreamingResponseParserReturnsLlamaParser() {
        let model = AIMetadata.Model(
            name: "llama3.3:latest",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://localhost:11434/api/chat",
            api: .llama,
            features: [.streaming, .functionCalling],
            vendor: .llama
        )
        let provider = LLMProvider(model: model)

        let parser = provider.streamingResponseParser(stream: true)
        XCTAssertTrue(parser is LlamaStreamingResponseParser)
    }

    func testStreamingResponseParserReturnsGeminiParser() {
        let model = AIMetadata.Model(
            name: "gemini-2.0-flash",
            contextWindowTokens: 1_048_576,
            maxResponseTokens: 8_192,
            url: "https://generativelanguage.googleapis.com/v1beta/models/{{MODEL}}",
            api: .gemini,
            features: [.functionCalling, .streaming],
            vendor: .gemini
        )
        let provider = LLMProvider(model: model)

        let parser = provider.streamingResponseParser(stream: true)
        XCTAssertTrue(parser is LLMGeminiStreamingResponseParser)
    }

    func testStreamingResponseParserReturnsNilWhenStreamFalse() {
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: [.functionCalling],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        // streamingResponseParser asserts stream=true, so we test with false
        // The function should return nil for stream=false
        let parser = provider.streamingResponseParser(stream: false)
        XCTAssertNil(parser)
    }

    // MARK: - LLMProvider.supportsStreaming

    func testSupportsStreamingReturnsTrueWhenFeatureEnabled() {
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: features,
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.supportsStreaming)
    }

    func testSupportsStreamingReturnsFalseWhenFeatureDisabled() {
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling]
        features.remove(.streaming)
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: features,
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertFalse(provider.supportsStreaming)
    }

    // MARK: - LLMProvider.supportsHostedWebSearch

    func testSupportsHostedWebSearchReturnsTrueWhenFeatureEnabled() {
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming, .hostedWebSearch]
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: features,
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.supportsHostedWebSearch)
    }

    func testSupportsHostedWebSearchReturnsFalseWhenFeatureDisabled() {
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: features,
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertFalse(provider.supportsHostedWebSearch)
    }

    // MARK: - LLMProvider.supportsPreviousResponseID

    func testSupportsPreviousResponseIDReturnsTrueForResponsesAPI() {
        let model = AIMetadata.Model(
            name: "gpt-5",
            contextWindowTokens: 400_000,
            maxResponseTokens: 128_000,
            url: "https://api.openai.com/v1/responses",
            api: .responses,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.supportsPreviousResponseID)
    }

    func testSupportsPreviousResponseIDReturnsFalseForChatCompletions() {
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertFalse(provider.supportsPreviousResponseID)
    }

    // MARK: - LLMProvider.urlIsValid

    func testURLIsValidReturnsTrueForValidURL() {
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertTrue(provider.urlIsValid)
    }

    func testURLIsValidReturnsFalseForInvalidURL() {
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "",
            api: .chatCompletions,
            features: [.functionCalling, .streaming],
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertFalse(provider.urlIsValid)
    }

    // MARK: - LLMProvider.url() for Gemini

    func testGeminiURLBuildsCorrectPath() {
        let model = AIMetadata.Model(
            name: "gemini-2.0-flash",
            contextWindowTokens: 1_048_576,
            maxResponseTokens: 8_192,
            url: "https://generativelanguage.googleapis.com/v1beta/models/{{MODEL}}",
            api: .gemini,
            features: [.functionCalling, .streaming],
            vendor: .gemini
        )
        let provider = LLMProvider(model: model)

        let url = provider.url(apiKey: "test-key", streaming: false)
        XCTAssertTrue(url.absoluteString.contains("generativelanguage.googleapis.com"))
        XCTAssertTrue(url.absoluteString.contains("gemini-2.0-flash"))
        XCTAssertTrue(url.absoluteString.contains(":generateContent"))
        XCTAssertTrue(url.absoluteString.contains("key=test-key"))
    }

    func testGeminiURLBuildsCorrectStreamingPath() {
        let model = AIMetadata.Model(
            name: "gemini-2.0-flash",
            contextWindowTokens: 1_048_576,
            maxResponseTokens: 8_192,
            url: "https://generativelanguage.googleapis.com/v1beta/models/{{MODEL}}",
            api: .gemini,
            features: [.functionCalling, .streaming],
            vendor: .gemini
        )
        let provider = LLMProvider(model: model)

        let url = provider.url(apiKey: "test-key", streaming: true)
        XCTAssertTrue(url.absoluteString.contains(":streamGenerateContent"))
        XCTAssertTrue(url.absoluteString.contains("alt=sse"))
    }

    // MARK: - LLMProvider.createVectorStoreURL

    func testCreateVectorStoreURLReturnsNilForDisabled() {
        let model = AIMetadata.Model(
            name: "gpt-4o",
            contextWindowTokens: 128_000,
            maxResponseTokens: 16_384,
            url: "https://api.openai.com/v1/chat/completions",
            api: .chatCompletions,
            features: [.functionCalling, .streaming],
            vectorStoreConfig: .disabled,
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        XCTAssertNil(provider.createVectorStoreURL(apiKey: "test-key"))
    }

    func testCreateVectorStoreURLReturnsOpenAIURL() {
        let model = AIMetadata.Model(
            name: "gpt-5",
            contextWindowTokens: 400_000,
            maxResponseTokens: 128_000,
            url: "https://api.openai.com/v1/responses",
            api: .responses,
            features: [.functionCalling, .streaming],
            vectorStoreConfig: .openAI,
            vendor: .openAI
        )
        let provider = LLMProvider(model: model)

        let url = provider.createVectorStoreURL(apiKey: "test-key")
        XCTAssertEqual(url?.absoluteString, "https://api.openai.com/v1/vector_stores")
    }

    // MARK: - MIMETypeIsTextual

    func testMIMETypeIsTextualReturnsTrueForTextTypes() {
        XCTAssertTrue(MIMETypeIsTextual("text/plain"))
        XCTAssertTrue(MIMETypeIsTextual("text/html"))
        XCTAssertTrue(MIMETypeIsTextual("text/css"))
        XCTAssertTrue(MIMETypeIsTextual("text/csv"))
    }

    func testMIMETypeIsTextualReturnsTrueForJSON() {
        XCTAssertTrue(MIMETypeIsTextual("application/json"))
    }

    func testMIMETypeIsTextualReturnsTrueForJavaScript() {
        XCTAssertTrue(MIMETypeIsTextual("application/javascript"))
        XCTAssertTrue(MIMETypeIsTextual("application/ecmascript"))
    }

    func testMIMETypeIsTextualReturnsTrueForXML() {
        XCTAssertTrue(MIMETypeIsTextual("application/xml"))
        XCTAssertTrue(MIMETypeIsTextual("application/xhtml+xml"))
        XCTAssertTrue(MIMETypeIsTextual("image/svg+xml"))
    }

    func testMIMETypeIsTextualReturnsTrueForRFC822() {
        XCTAssertTrue(MIMETypeIsTextual("message/rfc822"))
    }

    func testMIMETypeIsTextualReturnsTrueForSQL() {
        XCTAssertTrue(MIMETypeIsTextual("application/x-sql"))
    }

    func testMIMETypeIsTextualReturnsTrueForTeX() {
        XCTAssertTrue(MIMETypeIsTextual("application/x-tex"))
        XCTAssertTrue(MIMETypeIsTextual("application/x-texi"))
    }

    func testMIMETypeIsTextualReturnsFalseForBinaryTypes() {
        XCTAssertFalse(MIMETypeIsTextual("application/octet-stream"))
        XCTAssertFalse(MIMETypeIsTextual("image/png"))
        XCTAssertFalse(MIMETypeIsTextual("image/jpeg"))
        XCTAssertFalse(MIMETypeIsTextual("video/mp4"))
        XCTAssertFalse(MIMETypeIsTextual("audio/mpeg"))
    }

    // MARK: - Edge Cases: functionsSupported

    func testFunctionsSupportedForLlamaWithBothOllamaAndOpenAIURLs() {
        // Same model name, different URLs should give different results
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]

        let ollamaModel = AIMetadata.Model(
            name: "llama3.3:latest",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://localhost:11434/api/chat",
            api: .llama,
            features: features,
            vendor: .llama
        )
        let ollamaProvider = LLMProvider(model: ollamaModel)

        let llamaServerModel = AIMetadata.Model(
            name: "llama3.3:latest",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://localhost:8001/v1/chat/completions",
            api: .chatCompletions,
            features: features,
            vendor: .llama
        )
        let llamaServerProvider = LLMProvider(model: llamaServerModel)

        // Ollama native API with streaming → false
        XCTAssertFalse(ollamaProvider.functionsSupported)

        // llama-server OpenAI-compatible API with streaming → true
        // Note: This uses .chatCompletions API type, not .llama, so the check is different
        XCTAssertTrue(llamaServerProvider.functionsSupported)
    }

    func testFunctionsSupportedForLlamaAPIWithNonOllamaURL() {
        // Edge case: .llama API type but URL is NOT Ollama native
        // This shouldn't happen in practice but should still work
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "llama3.3:latest",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://localhost:8001/v1/chat/completions",
            api: .llama,
            features: features,
            vendor: .llama
        )
        let provider = LLMProvider(model: model)

        // URL doesn't contain /api/chat or /api/generate, so it's not Ollama native
        // Should return true (functionCalling feature is enabled)
        XCTAssertTrue(provider.functionsSupported)
    }

    func testFunctionsSupportedForLlamaAPIWithGenerateEndpoint() {
        // Ollama's /api/generate endpoint should also block function calling with streaming
        var features: Set<AIMetadata.Model.Feature> = [.functionCalling, .streaming]
        let model = AIMetadata.Model(
            name: "llama3.3:latest",
            contextWindowTokens: 131_072,
            maxResponseTokens: 131_072,
            url: "http://localhost:11434/api/generate",
            api: .llama,
            features: features,
            vendor: .llama
        )
        let provider = LLMProvider(model: model)

        XCTAssertFalse(provider.functionsSupported)
    }
}
