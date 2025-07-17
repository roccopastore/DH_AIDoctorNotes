from moviepy import ImageClip, concatenate_videoclips, AudioFileClip
import numpy as np
import librosa
from pyt2s.services import stream_elements
import os
import random
import soundfile as sf # Added to save the trimmed audio
import json
import requests


def who_starts(conversation):
    """
    Determines if the conversation starts with the Doctor or the Patient.
    Returns 'D' for Doctor, 'P' for Patient, or None if unclear.
    """
    lines = conversation.strip().split('\n')

    if not lines or not lines[0].strip():
        print("The conversation is empty or the first line is empty.")
        return None
    else:
        # Get the first line and remove any leading/trailing whitespace.
        # This is important because lines in the original string might have leading spaces.
        first_line = lines[0].strip()

        if first_line.startswith("DOCTOR:"):
            return "D"
        elif first_line.startswith("PATIENT:"):
            return "P"
        return None

def request_video(conversation, timestamp):
    """
    Sends a request to the Synthesia API to generate a video from a template
    based on the provided conversation.
    """
    print("REQUESTING VIDEO")
    # print(conversation)
    doctor_lines = []
    patient_lines = []

    start = who_starts(conversation)
    if start == "P":
        # If the patient starts, add a placeholder for the doctor's first line.
        doctor_lines.append("-")
    print(f"Starting speaker: {start}")

    # Synthesia template IDs based on dialogue length
    templates = ["aabf51e2-6b32-4cf1-bf63-5a02aa992ad9", "18f9fd5f-44d5-4f6c-b257-e296f2be3253", "ceb5f416-a46f-47d6-aae5-69b9ef4ce847", "54564e54-1294-45eb-ab88-8178a17a016c"]
    dialogue_length_tiers = [5, 10, 15, 20]

    lines = conversation.strip().split('\n')

    for line in lines:
        line = line.strip() # Remove leading/trailing whitespace from the line
        if line.startswith("DOCTOR:"):
            # Extract text after "DOCTOR: "
            doctor_lines.append(line[len("DOCTOR: "):].strip())
        elif line.startswith("PATIENT:"):
            # Extract text after "PATIENT: "
            patient_lines.append(line[len("PATIENT: "):].strip())

    num_dialogue = max(len(doctor_lines), len(patient_lines))
    print("Number of lines: " + str(num_dialogue))

    # Select the appropriate template index based on the number of dialogue lines
    index = 0
    if num_dialogue > 5 and num_dialogue <= 10:
        index = 1
    elif num_dialogue > 10 and num_dialogue <= 15:
        index = 2
    elif num_dialogue > 15:
        index = 3

    # Build the payload for the API request
    generated_text = {}
    i = 1
    while i < dialogue_length_tiers[index] + 1:
        generated_text[f"doctor_text_{i}"] = doctor_lines[i-1] if len(doctor_lines) >= i else "-"
        generated_text[f"patient_text_{i}"] = patient_lines[i-1] if len(patient_lines) >= i else "-"
        i += 1

    print(generated_text)
    payload = {
        "test": False,
        "templateData": generated_text,
        "visibility": "public",
        "templateId": templates[index]
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "your_key" # Synthesia API Key
    }

    url = "https://api.synthesia.io/v2/videos/fromTemplate"

    print("--- Generated Payload ---")
    print(json.dumps(payload, indent=4)) # Use json.dumps for a readable print

    print("\n--- Generated Headers ---")
    print(json.dumps(headers, indent=4))

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    print(data)

    # Save the video ID to a file for later polling
    with open(f"./backend/output/saves/{timestamp}/id.txt", "w", encoding="utf-8") as file:
        if data.get("id") is not None:
            file.write(data["id"])
        else:
            file.write("NO ID")

def info_video(video_id, timestamp):
    """
    Polls the Synthesia API to check the status of a video generation job.
    If complete, it triggers the download.
    """

    url = f"https://api.synthesia.io/v2/videos/{video_id}"
    headers = {
        "accept": "application/json",
        "Authorization": "your_key"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(data)
        if data.get("status") == "complete":
            download_video(data.get("download"), timestamp)
            return True
    return False

import sys

def download_video(download_url, timestamp):
    """
    Downloads a video from a given URL and saves it to the specified path
    with a progress bar.
    """
    headers = {
        "accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(download_url, headers=headers, stream=True)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(e)
        print(response.text)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    downloaded_size = 0
    output_path = f"./backend/output/saves/{timestamp}/video.mp4"

    print(f"Starting download.. {download_url}", file=sys.stderr)
    print(f"Saving in... {output_path}", file=sys.stderr)

    with open(output_path, 'wb') as file:
        for data in response.iter_content(block_size):
            file.write(data)
            downloaded_size += len(data)
            if total_size > 0:
                progress = int(50 * downloaded_size / total_size)
                sys.stderr.write(f"\r[{'=' * progress}{' ' * (50 - progress)}] {downloaded_size}/{total_size} bytes")
                sys.stderr.flush()

    sys.stderr.write("\n")
    print("Download complete!", file=sys.stderr)

def generate_speech(text, voice, filename):
    """Generates an audio file from text using the specified voice."""
    try:
        data = stream_elements.requestTTS(text, voice.value)
        with open(filename, '+wb') as file:
            file.write(data)
        return filename
    except Exception as e:
        print(f"Error during speech generation for '{text[:30]}...': {e}")
        print("Ensure the pyt2s library is configured correctly and there is an internet connection.")
        raise

def create_talking_avatar_clip(audio_path, img_array_open, img_closed, frame_rate_s):
    """
    Creates a video clip of a talking avatar, synchronized with an audio file.
    The avatar alternates between open-mouth images when there is sound and
    a closed-mouth image during silence.
    """
    try:
        y, sr = librosa.load(audio_path, sr=None)
    except Exception as e:
        print(f"Error loading {audio_path} with librosa: {e}")
        raise

    audio_clip_obj = AudioFileClip(audio_path)
    duration = audio_clip_obj.duration

    # Handle very short or silent audio clips
    if duration <= (1 / frame_rate_s):
        min_duration = 1 / frame_rate_s
        print(f"  Warning: Audio duration in create_talking_avatar_clip ({audio_path}) is minimal or zero ({duration:.3f}s). Creating a single static frame of {min_duration:.3f}s.")
        clip_frame = ImageClip(img_closed).with_duration(min_duration)
        try:
            video_segment = clip_frame.with_audio(audio_clip_obj)
        except Exception:
            video_segment = clip_frame
        return video_segment

    # Calculate RMS (root-mean-square) to detect sound
    frame_length_librosa = 2048
    hop_length_librosa = 512
    rms = librosa.feature.rms(y=y, frame_length=frame_length_librosa, hop_length=hop_length_librosa)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length_librosa)
    
    video_frames = []
    current_time = 0
    threshold_rms = 0.01
    
    mouth_change_interval = 0.1  # How often the mouth image can change
    last_mouth_change_time = 0
    current_mouth_image = img_closed
    
    # Generate video frames based on audio volume
    while current_time < duration:
        rms_index = min(np.argmin(np.abs(times - current_time)), len(rms) - 1)
        is_speaking_now = rms[rms_index] > threshold_rms
        
        if current_time - last_mouth_change_time >= mouth_change_interval:
            current_mouth_image = random.choice(img_array_open) if is_speaking_now else img_closed
            last_mouth_change_time = current_time

        clip_frame = ImageClip(current_mouth_image).with_duration(1 / frame_rate_s)
        video_frames.append(clip_frame)
        current_time += 1 / frame_rate_s

    if not video_frames: # Ensure there's at least one frame
        video_frames.append(ImageClip(img_closed).with_duration(duration))

    video_segment = concatenate_videoclips(video_frames, method="chain").with_audio(audio_clip_obj)
    return video_segment

# --- 3. Function to parse the conversation input ---
def parse_conversation_input(input_string):
    """
    Parses an input string in the format "SPEAKER:text\nSPEAKER:text"
    and returns a list of dictionaries.
    """
    parsed_conversation = []
    lines = input_string.strip().split('\n')
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        if ':' not in line:
            print(f"Error on line {line_num + 1}: '{line}'. Invalid format. Must be 'SPEAKER:text'.")
            return None # Return None to indicate a parsing error
        
        parts = line.split(':', 1) # Split only at the first ':'
        speaker_raw = parts[0].strip().upper() # Remove spaces and convert to uppercase
        text = parts[1].strip()

        # Map raw speaker names to consistent names
        speaker_map = {"PATIENT": "Patient", "DOCTOR": "Doctor"}
        speaker_name = speaker_map.get(speaker_raw, speaker_raw) # Use the mapped name or the raw one

        parsed_conversation.append({"speaker": speaker_name, "text": text})
            
    return parsed_conversation

# --- 4. Define avatar resources (voices and images) ---
FRAME_RATE = 30  # Increased for more fluidity
TARGET_HEIGHT = 720  # HD (720p)

# --- 5. Main function for processing the conversation ---
def process_conversation_and_create_video(conversation_data, folder, female):
    """
    Main function to process the conversation data and create the final video.
    """
    all_scene_clips = []
    temp_audio_files = []

    IMG_PATIENT_OPEN_1 = ""
    IMG_PATIENT_OPEN_2 = ""
    IMG_PATIENT_OPEN_3 = ""
    IMG_PATIENT_CLOSED = ""

    IMG_DOCTOR_OPEN_1 = ""
    IMG_DOCTOR_OPEN_2 = ""
    IMG_DOCTOR_OPEN_3 = "" 
    IMG_DOCTOR_CLOSED = ""

    # Definition of image paths
    if female:
        IMG_PATIENT_OPEN_1 = "./avatars/patient_avatar/female_avatar/image_with_doctor_move1.png"
        IMG_PATIENT_OPEN_2 = "./avatars/patient_avatar/female_avatar/image_with_doctor_move2.png"
        IMG_PATIENT_OPEN_3 = "./avatars/patient_avatar/female_avatar/image_with_doctor_move3.png"
        IMG_PATIENT_CLOSED = "./avatars/patient_avatar/female_avatar/image_with_doctor_base.png"

        IMG_DOCTOR_OPEN_1 = "./avatars/doctor_avatar/female/image_with_girl_move1.png"
        IMG_DOCTOR_OPEN_2 = "./avatars/doctor_avatar/female/image_with_girl_move2.png"
        IMG_DOCTOR_OPEN_3 = "./avatars/doctor_avatar/female/image_with_girl_move3.png" 
        IMG_DOCTOR_CLOSED = "./avatars/doctor_avatar/female/image_with_girl_base.png"
        patient_voice = stream_elements.Voice.Emma
    else:
        IMG_PATIENT_OPEN_1 = "./avatars/patient_avatar/male_avatar/image_with_man_move1.png"
        IMG_PATIENT_OPEN_2 = "./avatars/patient_avatar/male_avatar/image_with_man_move2.png"
        IMG_PATIENT_OPEN_3 = "./avatars/patient_avatar/male_avatar/image_with_man_move3.png"
        IMG_PATIENT_CLOSED = "./avatars/patient_avatar/male_avatar/image_with_man_base.png"

        IMG_DOCTOR_OPEN_1 = "./avatars/doctor_avatar/male/image_with_doctor_man_move1.png"
        IMG_DOCTOR_OPEN_2 = "./avatars/doctor_avatar/male/image_with_doctor_man_move2.png"
        IMG_DOCTOR_OPEN_3 = "./avatars/doctor_avatar/male/image_with_doctor_man_move3.png" 
        IMG_DOCTOR_CLOSED = "./avatars/doctor_avatar/male/image_with_doctor_man_base.png"
        patient_voice = stream_elements.Voice.Matthew

    SPEAKER_RESOURCES = {
        "Patient": {
            "voice": patient_voice,
            "open_images": [IMG_PATIENT_OPEN_1, IMG_PATIENT_OPEN_2, IMG_PATIENT_OPEN_3],
            "closed_image": IMG_PATIENT_CLOSED
        },
        "Doctor": {
            "voice": stream_elements.Voice.Brian,
            "open_images": [IMG_DOCTOR_OPEN_1, IMG_DOCTOR_OPEN_2, IMG_DOCTOR_OPEN_3], 
            "closed_image": IMG_DOCTOR_CLOSED
        }
    }

    print("Starting conversation processing...")
    for i, turn in enumerate(conversation_data):
        speaker = turn["speaker"]
        text = turn["text"]
        
        if speaker not in SPEAKER_RESOURCES:
            print(f"Warning: Speaker '{speaker}' not recognized. Skipping this turn.")
            continue
        
        resources = SPEAKER_RESOURCES[speaker]
        print(f"Turn {i+1}: {speaker} says '{text[:50]}...'")
        
        raw_audio_filename = f"temp_audio_turn_{i}_raw.mp3"
        trimmed_audio_filename = f"temp_audio_turn_{i}_trimmed.wav"
        
        try:
            # 1. Generate raw speech
            generate_speech(text, resources["voice"], raw_audio_filename)
            temp_audio_files.append(raw_audio_filename)

            # 2. Load raw audio with Librosa
            y_raw, sr = librosa.load(raw_audio_filename, sr=None)

            # 3. Trim silences
            y_trimmed, index = librosa.effects.trim(y_raw, top_db=25)

            print(f"  Raw audio duration: {len(y_raw)/sr:.2f}s")
            print(f"  Trimmed audio duration: {len(y_trimmed)/sr:.2f}s" if len(y_trimmed) > 0 else "  Trimmed audio is empty.")

            if len(y_trimmed) == 0:
                print(f"  Warning: Audio for turn {i+1} ('{text[:20]}...') was completely silent after trimming. Using original audio.")
                audio_for_animation_path = raw_audio_filename
            else:
                # 4. Save the trimmed audio to a .wav file
                sf.write(trimmed_audio_filename, y_trimmed, sr)
                temp_audio_files.append(trimmed_audio_filename)
                audio_for_animation_path = trimmed_audio_filename
            
            with AudioFileClip(audio_for_animation_path) as temp_clip:
                turn_duration = temp_clip.duration
            if turn_duration <= 0:
                print(f"  Warning: Audio duration for turn {i+1} is <= 0. Setting to 0.1s.")
                turn_duration = 0.1

        except Exception as e:
            print(f"Could not generate, load, or trim audio for turn {i+1}. Skipping this turn. Error: {e}")
            if os.path.exists(raw_audio_filename) and raw_audio_filename not in temp_audio_files:
                 temp_audio_files.append(raw_audio_filename)
            if os.path.exists(trimmed_audio_filename) and trimmed_audio_filename not in temp_audio_files:
                 temp_audio_files.append(trimmed_audio_filename)
            continue

        print(f"  Creating talking clip for {speaker} (trimmed duration: {turn_duration:.2f}s)")
        current_scene = create_talking_avatar_clip(audio_for_animation_path, resources["open_images"], resources["closed_image"], FRAME_RATE)
        
        current_scene_resized = current_scene.resized(height=TARGET_HEIGHT)
        all_scene_clips.append(current_scene_resized)

    # --- 6. Combine all scenes and write the final video ---
    if not all_scene_clips:
        print("No scenes were created. Exiting.")
    else:
        print("Combining all scenes...")
        final_video = concatenate_videoclips(all_scene_clips, method="chain")
        
        output_filename = f"./backend/output/saves/{folder}/videoT.mp4"
        print(f"Writing final video to {output_filename}...")
        try:
            final_video.write_videofile(
                output_filename,
                fps=FRAME_RATE,
                codec="libx264",
                audio_codec="aac",
                bitrate="8000k",
                audio_bitrate="320k",
                preset="slow",
                ffmpeg_params=["-crf", "18"]
            )
            print(f"Final video saved as {output_filename}")
        except Exception as e:
            print(f"Error writing final video: {e}")
            print("You may need to install ffmpeg or specify the correct path.")

        # Clean up moviepy resources
        if 'final_video' in locals() and final_video is not None:
            final_video.close()
        for scene_clip in all_scene_clips:
            scene_clip.close()

    # --- 7. Clean up temporary audio files ---
    print("Cleaning up temporary audio files...")
    for f_path in temp_audio_files:
        if os.path.exists(f_path):
            try:
                os.remove(f_path)
                print(f"  Removed: {f_path}")
            except Exception as e:
                print(f"  Error removing {f_path}: {e}")


def handle_video(conversation, timestamp, female):
    """
    Main handler to orchestrate the video generation process.
    """
    parsed_conversation = parse_conversation_input(conversation)
    # Request the high-quality video from Synthesia API in parallel
    request_video(conversation, timestamp)
    # Generate the local low-quality preview
    if parsed_conversation:
        process_conversation_and_create_video(parsed_conversation, timestamp, female)
    else:
        print("Could not proceed due to an error in parsing the conversation input.")


