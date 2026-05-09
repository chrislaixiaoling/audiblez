#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audiblez HF Spaces - Gradio Web UI for epub to audiobook conversion
"""
import shutil
import tempfile
from pathlib import Path

import gradio as gr
import numpy as np
import soundfile as sf
from kokoro import KPipeline
import spacy

from audiblez.core import (
    find_document_chapters_and_extract_texts,
    find_good_chapters,
    find_cover,
    gen_audio_segments,
    load_spacy,
)

sample_rate = 24000

# Supported voices for HF Spaces (simplified list)
SUPPORTED_VOICES = {
    "🇺🇸 美式英语 - af_sky": ("a", "af_sky"),
    "🇺🇸 美式英语 - af_heart": ("a", "af_heart"),
    "🇺🇸 美式英语 - af_bella": ("a", "af_bella"),
    "🇺🇸 美式英语 - am_adam": ("a", "am_adam"),
    "🇺🇸 美式英语 - am_onyx": ("a", "am_onyx"),
    "🇬🇧 英式英语 - bf_emma": ("b", "bf_emma"),
    "🇬🇧 英式英语 - bm_george": ("b", "bm_george"),
    "🇪🇸 西班牙语 - ef_dora": ("e", "ef_dora"),
    "🇫🇷 法语 - ff_siwis": ("f", "ff_siwis"),
    "🇮🇹 意大利语 - if_sara": ("i", "if_sara"),
    "🇧🇷 葡萄牙语 - pf_dora": ("p", "pf_dora"),
    "🇨🇳 中文 - zf_xiaobei": ("z", "zf_xiaobei"),
    "🇨🇳 中文 - zf_xiaoni": ("z", "zf_xiaoni"),
    "🇨🇳 中文 - zm_yunxi": ("z", "zm_yunxi"),
    "🇨🇳 中文 - zm_yunxia": ("z", "zm_yunxia"),
    "🇯🇵 日语 - jf_alpha": ("j", "jf_alpha"),
    "🇮🇳 印地语 - hf_alpha": ("h", "hf_alpha"),
}


def process_epub(epub_file, voice_choice, speed, progress_callback=None):
    """Process epub file and generate audiobook"""
    if epub_file is None:
        return None, "请上传 epub 文件"

    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy epub to temp dir
        epub_path = Path(temp_dir) / "input.epub"
        shutil.copy(epub_file, epub_path)

        # Load spacy model
        load_spacy()

        # Parse epub
        from ebooklib import epub
        book = epub.read_epub(str(epub_path))
        meta_title = book.get_metadata('DC', 'title')
        title = meta_title[0][0] if meta_title else 'Unknown'
        meta_creator = book.get_metadata('DC', 'creator')
        creator = meta_creator[0][0] if meta_creator else 'Unknown'

        # Get cover
        cover_maybe = find_cover(book)
        cover_image = cover_maybe.get_content() if cover_maybe else b""

        # Get chapters
        document_chapters = find_document_chapters_and_extract_texts(book)
        selected_chapters = find_good_chapters(document_chapters)

        if not selected_chapters:
            return None, "未找到可用章节"

        texts = [c.extracted_text for c in selected_chapters]
        total_chars = sum(map(len, texts))

        # Get voice
        lang_code, voice = voice_choice

        # Setup pipeline
        pipeline = KPipeline(lang_code=lang_code)

        # Generate audio for each chapter
        chapter_wav_files = []
        for i, chapter in enumerate(selected_chapters, start=1):
            text = chapter.extracted_text
            if len(text.strip()) < 10:
                continue

            # Add intro for first chapter
            if i == 1:
                text = f'{title} – {creator}.\n\n' + text

            # Generate audio
            wav_path = Path(temp_dir) / f"chapter_{i}.wav"
            audio_segments = gen_audio_segments(
                pipeline, text, (lang_code, voice), speed
            )
            if audio_segments:
                final_audio = np.concatenate(audio_segments)
                sf.write(str(wav_path), final_audio, sample_rate)
                chapter_wav_files.append(wav_path)

            if progress_callback:
                progress_callback(i / len(selected_chapters))

        # Create m4b
        m4b_path = Path(temp_dir) / f"{title}.m4b"
        create_m4b_for_spaces(chapter_wav_files, m4b_path, cover_image, title, creator)

        # Copy to output
        output_path = Path(temp_dir) / f"{title}_audiobook.m4b"
        shutil.copy(m4b_path, output_path)

        return str(output_path), f"完成！生成 {len(chapter_wav_files)} 章，共 {total_chars:,} 字符"


def create_m4b_for_spaces(chapter_files, output_path, cover_image, title, creator):
    """Create m4b file from wav chapters"""
    import subprocess

    if not chapter_files:
        return

    # Concatenate wavs
    concat_list = Path(output_path.parent) / "concat_list.txt"
    with open(concat_list, 'w') as f:
        for wav in chapter_files:
            f.write(f"file '{wav}'\n")

    concat_wav = Path(output_path.parent) / "concat.wav"
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', str(concat_list), '-c', 'pcm_s16le', str(concat_wav)
    ], capture_output=True)

    # Create m4b
    if cover_image:
        cover_path = Path(output_path.parent) / "cover.jpg"
        with open(cover_path, 'wb') as f:
            f.write(cover_image)
        cover_args = ['-i', str(cover_path), '-map', '0:v', '-disposition:v', 'attached_pic']
    else:
        cover_args = []

    subprocess.run([
        'ffmpeg', '-y',
        '-i', str(concat_wav),
        *cover_args,
        '-c:a', 'aac', '-b:a', '64k',
        '-map_metadata', '-1',
        '-f', 'mp4', str(output_path)
    ], capture_output=True)


def get_book_info(epub_file):
    """Extract book info from epub"""
    if epub_file is None:
        return "", "", 0

    from ebooklib import epub
    book = epub.read_epub(epub_file)

    meta_title = book.get_metadata('DC', 'title')
    title = meta_title[0][0] if meta_title else 'Unknown'

    meta_creator = book.get_metadata('DC', 'creator')
    creator = meta_creator[0][0] if meta_creator else 'Unknown'

    document_chapters = find_document_chapters_and_extract_texts(book)
    selected_chapters = find_good_chapters(document_chapters)

    total_chars = sum(len(c.extracted_text) for c in selected_chapters)

    return title, creator, total_chars


# Gradio UI
with gr.Blocks(title="Audiblez - Epub转有声书", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎧 Audiblez - Epub转有声书")
    gr.Markdown("基于 Kokoro-82M TTS 模型，将 epub 电子书转换为 m4b 有声书")

    with gr.Row():
        with gr.Column(scale=1):
            epub_input = gr.File(
                label="上传 Epub 文件",
                file_types=[".epub"],
                file_count=1
            )

            book_info = gr.Markdown("---")

            voice_choice = gr.Dropdown(
                choices=list(SUPPORTED_VOICES.keys()),
                value=list(SUPPORTED_VOICES.keys())[0],
                label="选择语音"
            )

            speed = gr.Slider(
                minimum=0.5,
                maximum=2.0,
                value=1.0,
                step=0.1,
                label="语速"
            )

            generate_btn = gr.Button("🎙️ 开始生成有声书", variant="primary")

        with gr.Column(scale=2):
            output_audio = gr.Audio(label="生成的有声书", type="filepath")
            status_text = gr.Textbox(label="状态", lines=3)

    # Event handlers
    epub_input.change(
        fn=get_book_info,
        inputs=[epub_input],
        outputs=[book_info]
    )

    generate_btn.click(
        fn=process_epub,
        inputs=[epub_input, voice_choice, speed],
        outputs=[output_audio, status_text]
    )

    grExamples = gr.Examples(
        examples=[],  # No examples as epub files are required
        label="使用说明"
    )

    gr.Markdown("""
    ### 使用说明
    1. 上传 epub 格式的电子书文件
    2. 选择喜欢的语音和语速
    3. 点击"开始生成有声书"按钮
    4. 等待生成完成后，点击音频播放器下载

    **注意**: 处理可能需要较长时间，请耐心等待。
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
