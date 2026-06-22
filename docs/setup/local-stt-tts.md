# Local STT/TTS

Fake STT and TTS are the default for deterministic local smoke tests.

```env
AI_STT_PROVIDER=fake
AI_TTS_PROVIDER=fake
```

## STT Options

| Provider | Env value | Notes |
| --- | --- | --- |
| Fake | `fake` | Deterministic CI/default path |
| Local Whisper | `whisper_local` | Python/local model path, hardware-dependent |
| whisper.cpp | `whisper_cpp` | External binary and model file |
| Deepgram | `deepgram` | Cloud STT, requires key |
| Custom | `custom` | Adapter-specific |

Local Whisper example:

```env
AI_STT_PROVIDER=whisper_local
WHISPER_LOCAL_MODEL=base
WHISPER_LOCAL_DEVICE=cpu
```

whisper.cpp example:

```env
AI_STT_PROVIDER=whisper_cpp
WHISPER_CPP_BINARY_PATH=/path/to/whisper-cli
WHISPER_CPP_MODEL_PATH=/path/to/model.bin
```

Cloud STT example:

```env
AI_STT_PROVIDER=deepgram
DEEPGRAM_API_KEY=<your-key>
DEEPGRAM_MODEL=<model>
DEEPGRAM_LANGUAGE=en
```

## TTS Options

| Provider | Env value | Notes |
| --- | --- | --- |
| Fake | `fake` | Deterministic CI/default path |
| Kokoro | `kokoro` | Local service profile |
| Piper | `piper` | External binary and model file |
| Cartesia | `cartesia` | Cloud TTS, requires key |
| Custom | `custom` | Adapter-specific |

Kokoro local service example:

```env
AI_TTS_PROVIDER=kokoro
KOKORO_BASE_URL=http://tts:8100
KOKORO_VOICE=af_heart
```

Run:

```bash
docker compose --profile tts-local up --build
```

Piper example:

```env
AI_TTS_PROVIDER=piper
PIPER_BINARY_PATH=/path/to/piper
PIPER_MODEL_PATH=/path/to/model.onnx
```

Cloud TTS example:

```env
AI_TTS_PROVIDER=cartesia
CARTESIA_API_KEY=<your-key>
CARTESIA_VOICE_ID=<voice-id>
```

## Hardware Guidance

Local STT/TTS can be slower than cloud providers on laptops. For an interview demo, prefer:

```env
AI_TEXT_PROVIDER=fake
AI_STT_PROVIDER=fake
AI_TTS_PROVIDER=fake
```

or use hosted text inference with fake voice:

```env
AI_TEXT_PROVIDER=nvidia_nim
AI_STT_PROVIDER=fake
AI_TTS_PROVIDER=fake
```
