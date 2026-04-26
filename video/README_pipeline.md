# Video-to-LLM AI Pipeline

This pipeline takes any `.mp4` video, watches the frames, listens to the spoken audio, generates a highly detailed scene summary, and automatically passes it to Google Gemini to quiz you!

## Quick Setup

1. **Create an Environment:**
   *(We highly recommend using Conda or a Python `venv`)*
   ```bash
   conda create -n vlm2vec python=3.10
   conda activate vlm2vec
   ```

2. **Install Dependencies:**
   Install all the required ML models, APIs, and audio processors.
   ```bash
   pip install -r requirements_pipeline.txt
   ```

3. **Install FFmpeg (Mac requirement for Whisper):**
   ```bash
   brew install ffmpeg
   ```

4. **Add Your Gemini API Key:**
   Make a copy of the `.env` template file, or manually create a file called `.env` in this directory containing:
   ```env
   GEMINI_API_KEY=YOUR_ACTUAL_API_KEY
   ```

## How to Run

Pass any `.mp4` video into the script!
```bash
python pipeline_video_to_llm.py your_video.mp4
```

> **Note 1 (First Run Downloads):** The very first time you run this, it will download several gigabytes of Qwen2-VL vision models to your computer. Please be patient while it caches the weights!
> 
> **Note 2 (Apple Silicon Macs):** If you are running this on an M-series Mac, the very first run will take an **extra 5 to 10 minutes** to launch. This is because Apple's Neural Engine Compiler must translate the massive PyTorch model into Metal Shaders in the background. Once compiled, future runs will start instantly.
> 
> **Note 3 (Chunking & Memory):** The pipeline now dynamically breaks the video into **10-second chunks**, optimizing memory usage so you can process extremely long videos without crashing or running out of RAM!
