import pyaudio
import wave
import threading
import time
import librosa
import noisereduce as nr
from pydub import AudioSegment
import soundfile as sf
import io
import assemblyai as aai
import requests
import re
import numpy as np
import os
from datetime import datetime
current_date = datetime.today().strftime("%d %B %Y")  # esempio: "13 May 2025"


FORMAT = pyaudio.paInt16  # 16-bit
CHANNELS = 1              # Mono
RATE = 44100              # Frequenza di campionamento (Hz)
CHUNK = 1024              # Buffer size 
recording = False
frames = []
stream = None
thread = None
start_time = 0
audio = None

def start_recording():

    global recording, thread, stream, audio, frames, start_time

    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    
    print("REGISTRAZIONE IN CORSO...")
    frames = []

    recording = True
    thread = threading.Thread(target=_record_audio)
    thread.start()

def _record_audio():
    
    global recording, stream, frames

    while recording:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        except OSError as e:
            print(f"Error: {e}")
            break

def stop_recording(output_time):
    global audio, stream, frames, recording, thread

    recording = False  # <-- Fermo il thread
    if thread is not None:
        thread.join()  # <-- Aspetto che finisca
        thread = None

    time.sleep(0.1)

    if stream is not None:
        stream.stop_stream()
        stream.close()
    if audio is not None:
        audio.terminate()

    if not frames:
        print("No audio recorded")
        return


    try:
        if audio is None:
            print("Audio object is not initialized.")
            return
        with wave.open(f'./backend/output/original_audio/{output_time}.wav', 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            print("File salvato")
    except Exception as e:
        print(f"Error {e}")
    finally:
        audio = None
        stream = None
        frames = []


def remove_noise(output_time):

    y, sr = librosa.load("./backend/output/original_audio/" + str(output_time) + ".wav", sr=None)

    y_denoised = nr.reduce_noise(y=y, sr=sr)

    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, y_denoised, sr, format='WAV') 

    audio = AudioSegment.from_wav(wav_buffer)
    wav_buffer.seek(0)
    audio_mp3 = audio.export(format="mp3").read()
    

    return audio_mp3

def get_sex_info(path):
    try:
        y, sr = librosa.load(path)

        f0, voiced_flag, voiced_probs = librosa.pyin(y, sr=sr, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C5'))

        f0 = f0[~np.isnan(f0)]

        if len(f0) == 0:
            return "Indefinito (Nessuna voce rilevata o pitch non chiaro)"

        mean_f0 = np.mean(f0)

        if mean_f0 < 150:  
            return False
        elif mean_f0 >= 150 and mean_f0 < 250: 
            return True
        else: 
            return True

    except Exception as e:
        return f"Errore durante l'elaborazione del file audio: {e}"


def transcript_audio(audio_file_name):

    aai.settings.api_key = "1323e6e9fdb049cebe3a50e1b80c3dab"

    #audio_file = "./backend/output/original_audio/" + audio_file_name + ".wav"

    # Esporta in formato WAV
    audio_file = "./backend/09  At The Doctors (mp3cut.net).mp3"
    audio_total = AudioSegment.from_mp3(audio_file)

    print(audio_total)
    
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        language_detection=True,
    )
    transcript = aai.Transcriber().transcribe(audio_file, config)
    print(transcript.__dict__)
    check = False
    string_to_ret = ""
    count = 0
    if not transcript.utterances is None:
        for utterance in transcript.utterances:
            print("UTTERANCE : " + str(utterance))
            string_to_ret += f"Speaker {utterance.speaker}: {utterance.text} \n"
            print(string_to_ret)
            if count < 2:
                audio_segment = audio_total[utterance.start:utterance.end]
                segment_path = f"./temp_files/segment_{utterance.speaker}.wav"
                audio_segment.export(segment_path, format="wav")
                female = get_sex_info(segment_path)
                print(female)
                if female:
                    check = True
            count += 1
                
    
    return string_to_ret, check


def analyze_dialogue(dialogue_text):

    TOGETHER_API_KEY = "b1ffe76016293ce862ba3477cae9ffb199b61f47fd2515d53a659f4cf2ff3c4e"  # crea gratis su https://together.ai

    prompt = f"""
        You are a virtual medical assistant.

You will be given a dialogue between a doctor and a patient. Your tasks are:

1. Identify who is the **Doctor** and who is the **Patient**.
2. **Ignore any third speaker** or any voice that is not clearly identifiable as Doctor or Patient.
3. **Fill in any missing or implied parts** of the conversation to ensure clarity and coherence.
4. **Rewrite the entire conversation** in a clear and readable format, labeling each line as "DOCTOR:" or "PATIENT:". Do not rewrite or paraphrase the content. Keep the original wording as much as possible. Only format and label the lines.
5. At the end, generate a summary section titled **[DOCTOR'S NOTES]** that includes:
   - Reported symptoms
   - Duration and severity
   - Possible diagnosis
   - Suggested follow-ups or tests

**Respect the language of the conversation to write the summary**
**Format your output as follows:**

[CONVERSATION]  
DOCTOR: ...  
PATIENT: ...  
...

[DOCTOR'S NOTES]  
- Reported symptoms: ...  
- Duration and severity: ...  
- Possible diagnosis: ...  
- Suggested follow-ups or tests: ...

Make sure the conversation flows naturally and is medically coherent, but **do not change the original meaning** of the dialogue and answer with the language of the conversation.

Conversation:  
{dialogue_text}

    """


    response = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        json={
            "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        },
    )
    print(response.json())
    text = response.json()["choices"][0]["message"]["content"]
    conversation_match = re.search(r"\[CONVERSATION\](.*?)\[DOCTOR'S NOTES\]", text, re.DOTALL)
    notes_match = re.search(r"\[DOCTOR'S NOTES\](.*)", text, re.DOTALL)

    conversation = conversation_match.group(1).strip() if conversation_match else ""
    doctor_notes = notes_match.group(1).strip() if notes_match else ""
    print(conversation)
    

    conversation_html = edit_color(conversation)

    return conversation_html, doctor_notes, conversation

def edit_color(conversation):
    
    html_output = ""

    lines = conversation.strip().split('\n')
    
    for line in lines:
        if line.startswith("DOCTOR:"):
            content = line.replace("DOCTOR:", "").strip()
            html_output += f'<p><span style="color: green; font-weight: bold">DOCTOR:</span> {content}</p>\n'
        elif line.startswith("PATIENT:"):
            content = line.replace("PATIENT:", "").strip()
            html_output += f'<p><span style="color: red; font-weight: bold">PATIENT:</span> {content}</p>\n'
        else:
            html_output += f'<p>{line}</p>\n'

    return html_output



def parse_medical_report(text):
    # I sottotitoli fissi (chiavi del dizionario)
    sections = [
        "Reported symptoms",
        "Duration and severity",
        "Possible diagnosis",
        "Suggested follow-ups or tests"
    ]

    # Crea un dizionario vuoto con i campi
    fields = {key: "" for key in sections}

    # Regex per suddividere il testo in base ai sottotitoli fissi
    pattern = r'(?P<section>' + '|'.join(re.escape(s) for s in sections) + r'):\s*'
    parts = re.split(pattern, text)

    # La prima parte è vuota, poi i dati seguono nel formato [section1, content1, section2, content2, ...]
    it = iter(parts[1:])
    for section, content in zip(it, it):
        if section in fields:
            fields[section] = content.strip()

    return fields


def generate_html_report(input_text):
    fields = parse_medical_report(input_text)
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Medical Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 2px;
                width: 450px;
            }}
            .report {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                max-width: 700px;
                margin: auto;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header img {{
                max-width: 30%;
                height: auto;
                display: block;
                margin-left: auto;
                margin-right: auto;
            }}
            .header-title {{
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 20px;
            }}
            h2 {{
                text-align: center;
            }}
            .meta-info {{
                display: flex;
                justify-content: space-between;
                font-size: 14px;
                color: #555;
                margin-bottom: 30px;
            }}
            .field {{
                margin-top: 20px;
                margin-bottom: 20px;
            }}
            .field label {{
                font-weight: bold;
                display: block;
                margin-bottom: 5px;
                border-bottom: 1px solid #ccc;
            }}
            .field p {{
                background: #f1f1f1;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="report">
            <div class="header">
                <img src={"./frontend/icons/logo_img_only.png"} width="75" alt="Logo">
                <div class="header-title">MEDICAL REPORT</div>
            </div>
            <div class="meta-info">
                <div><strong>Location:</strong>Università di Bologna, Bologna</div>
                <div><strong>Date:</strong>{current_date}</div>
            </div>
                {"".join(f'<div class="field"><label>{k}:</label><p>{v}</p></div>' for k, v in fields.items())}
        </div>
    </body>
    </html>
    """
    return html_template

import os

def save_files(conversation, notes, video, name):

    folder_path = f'./backend/output/saves/{name}'
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    conversation_path = os.path.join(folder_path, "conversation.txt")
    notes_path = os.path.join(folder_path, "notes.txt")


    with open(conversation_path, "w") as conversation_file:
        conversation_file.write(conversation)

    with open(notes_path, "w") as notes_file:
        notes_file.write(notes)

    print("Files done")