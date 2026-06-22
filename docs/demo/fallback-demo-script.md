# Fallback Demo Script

## Browser Failure

```text
I will switch from the external product URL to the local fixture app. This still exercises the controlled browser, screen reader, safety policy, cursor events, and grounded agent loop.
```

## Voice Failure

```text
I will switch to scripted text turns. This bypasses microphone/provider issues while exercising the same agent brain and browser runtime.
```

## Provider Failure

```text
I will switch to fake providers. The provider abstraction lets us separate infrastructure and browser orchestration from hosted model availability.
```

## Slow Hardware

```text
Local models can be slow on laptops. I will disable Ollama and observability and keep fake STT/TTS for the demo.
```
