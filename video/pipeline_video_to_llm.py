import os
import torch
import whisper
from moviepy import VideoFileClip
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import math
import gc

# If using an external API for the Text LLM, import it here:
# from openai import OpenAI

# ==========================================
# AUDIO EXTRACTION PIPELINE
# ==========================================
def extract_audio(video_path, audio_path="temp_audio.wav"):
    try:
        video = VideoFileClip(video_path)
        if video.audio is None:
            return None, video.duration
        video.audio.write_audiofile(audio_path, logger=None)
        return audio_path, video.duration
    except Exception as e:
        return None, 0.0

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    # Return the full result dictionary instead of just the text, 
    # so we have access to segment timestamps!
    result = model.transcribe(audio_path)
    return result


# ==========================================
# STEP 1: VIDEO -> TEXT (Captioning)
# ==========================================
def load_qwen_model():
    """Loads the Qwen model into memory once."""
    print("\n[INIT] Loading Qwen2-VL Model into memory (this may take a moment)...")
    model_id = "Qwen/Qwen2-VL-2B-Instruct"
    
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    
    import platform
    # Force 16-bit precision to save massively on RAM (fixes Mac OOM errors)
    if device == "mps" or device == "cuda":
        dtype = torch.float16 
    else:
        dtype = torch.float32
        
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id, 
        torch_dtype=dtype, 
        device_map="auto" if device == "cuda" else None
    )
    if device != "cuda":
        model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)
    return model, processor, device

def generate_video_summary_chunk(video_path, transcript_slice, start_time, end_time, model, processor, device):
    """Watches a specific 10-second chunk of the video and summarizes it."""
    
    prompt = (
        f"Watch this specific video segment from {start_time}s to {end_time}s. "
        "Provide a detailed, sequential breakdown of the visual events, spoken dialogue, and concepts discussed. "
        "Describe exactly what happens, but do NOT repeat yourself. If a scene is static, visually unchanging, or repetitive, describe it just once and state that it continues."
    )
    if transcript_slice:
        prompt += f" Here is the dialogue spoken during this segment: '{transcript_slice}'. Weave the dialogue into your summary."

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "video", 
                    "video": video_path, 
                    "video_start": start_time,
                    "video_end": end_time,
                    "max_pixels": 360 * 420, 
                    "fps": 0.5
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)

    inputs = processor(
        text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs, 
            max_new_tokens=1024, 
            repetition_penalty=1.1
        )
        
    generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
    
    output_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    
    # Force free memory after generating
    del image_inputs, video_inputs, inputs, generated_ids, generated_ids_trimmed
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    elif torch.backends.mps.is_available():
        torch.mps.empty_cache()
        
    return output_text[0]


# ==========================================
# STEP 2: TEXT -> QUESTIONS (Applying Generic Text LLM)
# ==========================================
def generate_questions_from_text(summary_text, transcript=""):
    """Feeds the detailed text summary and raw transcript into Google's Gemini LLM to build a quiz."""
    print("\n[STEP 2] Sending Mega-Context Summary & Transcript to Gemini LLM to generate questions...")
    
    from google import genai
    from dotenv import load_dotenv
    
    # 1. Load the variables from the .env file
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        return "[Error] API Key not found. Please add GEMINI_API_KEY to your .env file."
        
    # 2. Initialize the new Gemini Client
    client = genai.Client(api_key=api_key)
    
    # 3. Create the prompt
    prompt = (
        "You are a helpful teacher. Given the following comprehensive, chronological visual breakdown of a video, "
        "along with the exact spoken audio transcript, generate 5 highly challenging quiz questions "
        "to test a student's comprehensive understanding of the topic.\n\n"
        f"Chronological Visual Summary:\n{summary_text}\n\n"
    )
    if transcript:
        prompt += f"Complete Spoken Audio Transcript:\n{transcript}\n\n"
        
    # 4. Generate the response
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"[Gemini API Error] Please make sure you inserted your API key. Error details: {e}"


def get_transcript_slice(transcript_data, start_time, end_time):
    """Extracts spoken sentences that fall within [start_time, end_time]."""
    if not transcript_data or "segments" not in transcript_data:
        return ""
        
    slice_text = ""
    for segment in transcript_data["segments"]:
        # Allow slight overlap (e.g., if a word starts 0.5s before the chunk)
        if (segment["start"] < end_time and segment["end"] > start_time):
            slice_text += segment["text"] + " "
    return slice_text.strip()


def main():
    import sys
    
    # If the user provides a video path via terminal (e.g. `python pipeline_video_to_llm.py video.mp4`)
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Default fallback if no argument is given
        video_path = "10 sec 2D Test animation.mp4" 
    
    if not os.path.exists(video_path):
        print(f"Error: Could not find '{video_path}'")
        print("Usage: python pipeline_video_to_llm.py <path_to_video.mp4>")
        return

    # 1. AUDIO LAYER
    audio_file, duration = extract_audio(video_path)
    if duration == 0.0:
        # Fallback if duration extraction fails
        duration = 10.0

    transcript_data = None
    full_transcript = ""
    
    if audio_file:
        print("[STEP 0] Extracting Transcript with Whisper...")
        transcript_data = transcribe_audio(audio_file)
        full_transcript = transcript_data["text"]
        if os.path.exists(audio_file): os.remove(audio_file)
            
    # Load model once
    model, processor, device = load_qwen_model()
    
    # 2. VISION LAYER (Iterate sequentially in 10-second chunks)
    print(f"\n[STEP 1] Generating chunked summaries for {duration:.1f} seconds of video...")
    
    master_summary = ""
    chunk_size = 10
    total_chunks = math.ceil(duration / chunk_size)
    
    for i in range(total_chunks):
        start_time = i * chunk_size
        end_time = min((i + 1) * chunk_size, duration)
        
        print(f"  -> Processing Chunk {i + 1}/{total_chunks} [{start_time}s - {end_time}s]...")
        
        # Get audio strictly for this 10-second window
        slice_text = get_transcript_slice(transcript_data, start_time, end_time)
        
        # Ask Qwen to summarize this specific window
        chunk_summary = generate_video_summary_chunk(
            video_path, slice_text, start_time, end_time, model, processor, device
        )
        
        # Append to our master aggregated context
        master_summary += f"\n--- [Time: {start_time}s to {end_time}s] ---\n"
        master_summary += f"{chunk_summary}\n"
        
        # Explicit garbage collection to prevent memory bloat over iterations
        gc.collect()
    
    print("\n" + "="*40)
    print("OUTPUT FROM STEP 1 (The combined chunked Context given to LLM):")
    print("="*40)
    print(master_summary)
    print("="*40)
    
    # 3. TEXT LLM LAYER (Generate Questions)
    final_questions = generate_questions_from_text(master_summary, full_transcript)
    
    print("\n" + "="*40)
    print("OUTPUT FROM STEP 2 (The LLM generating questions):")
    print("="*40)
    print(final_questions)
    print("="*40)

if __name__ == "__main__":
    main()
