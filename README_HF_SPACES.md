# Audiblez - Epub to Audiobook Converter

<div align="center">

![Audiblez](https://img.shields.io/badge/Audiblez-v0.5.0-blue)
[![HuggingFace Spaces](https://img.shields.io/badge/🤗-HuggingFace%20Spaces-orange)](https://huggingface.co/spaces)

**Generate .m4b audiobooks from .epub e-books using Kokoro-82M TTS**

</div>

## Features

- 📚 Convert epub e-books to audiobook format (.m4b)
- 🗣️ Multiple voice options (English, Chinese, Spanish, French, Italian, Portuguese, Japanese, Hindi)
- 🎚️ Adjustable speech speed (0.5x - 2.0x)
- 🇺🇸🇬🇧🇨🇳 Support for 9 languages

## Supported Voices

| Language | Code | Sample Voices |
|----------|------|---------------|
| 🇺🇸 American English | `a` | af_sky, af_heart, am_adam |
| 🇬🇧 British English | `b` | bf_emma, bm_george |
| 🇨🇳 Chinese | `z` | zf_xiaobei, zm_yunxi |
| 🇪🇸 Spanish | `e` | ef_dora |
| 🇫🇷 French | `f` | ff_siwis |
| 🇮🇹 Italian | `i` | if_sara |
| 🇧🇷 Portuguese | `p` | pf_dora |
| 🇯🇵 Japanese | `j` | jf_alpha |
| 🇮🇳 Hindi | `h` | hf_alpha |

## Usage

1. Upload an epub file
2. Select your preferred voice
3. Adjust speech speed if needed
4. Click "Generate Audiobook"
5. Download the resulting .m4b file

## Technical Details

- **TTS Model**: [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) by hexgrad
- **Backend**: Gradio Web UI
- **Audio Format**: M4B with chapter markers

## Limitations

- CPU-only inference (may take 30-60 minutes for full books)
- File size limit depends on HuggingFace Spaces tier

## Local Development

```bash
# Build Docker image
docker build -t audiblez .

# Run
docker run -p 7860:7860 audiblez
```

## License

MIT License - See [LICENSE](LICENSE) for details.
