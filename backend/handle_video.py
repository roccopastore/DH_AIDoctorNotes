from moviepy import ImageClip, concatenate_videoclips, AudioFileClip
import numpy as np
import librosa
from pyt2s.services import stream_elements
import os
import random
import soundfile as sf # Aggiunto per salvare l'audio trimmato
import json
import requests


def who_starts(conversation):

    lines = conversation.strip().split('\n')

    if not lines or not lines[0].strip():
        print("La conversazione è vuota o la prima riga è vuota.")
    else:
        # Prendi la prima riga e rimuovi eventuali spazi bianchi iniziali/finali da essa.
        # Questo è importante perché le righe nella tua stringa originale hanno degli spazi davanti.
        first_line = lines[0].strip()

        if first_line.startswith("DOCTOR:"):
            return "D"
        elif first_line.startswith("PATIENT:"):
            return "P"

def request_video(conversation, timestamp):
    # Stringa da salvare
    id = "fdshfsdoidsohifs"

    # Apertura del file in modalità scrittura
    with open(f"./backend/output/saves/{timestamp}/id.txt", "w", encoding="utf-8") as file:
        file.write(id)

#     print("REQUEST VIDEO")
#     print(conversation)
#     doctor_lines = []
#     patient_lines = []

#     start = who_starts(conversation)
#     if start == "P":
#         doctor_lines.append("-")
#     print(f"{start} start")

#     templates = ["aabf51e2-6b32-4cf1-bf63-5a02aa992ad9", "18f9fd5f-44d5-4f6c-b257-e296f2be3253", "ceb5f416-a46f-47d6-aae5-69b9ef4ce847", "54564e54-1294-45eb-ab88-8178a17a016c"]
#     dialogues = [5,10,15,20]

#     lines = conversation.strip().split('\n')

#     for line in lines:
#         line = line.strip() # Rimuove spazi bianchi iniziali/finali dalla riga
#         if line.startswith("DOCTOR:"):
#             # Estrae il testo dopo "DOCTOR: "
#             doctor_lines.append(line[len("DOCTOR: "):].strip())
#         elif line.startswith("PATIENT:"):
#             # Estrae il testo dopo "PATIENT: "
#             patient_lines.append(line[len("PATIENT: "):].strip())

#     num_dialogue = max(len(doctor_lines), len(patient_lines))
#     print("Numero di battute: " + str(num_dialogue))

#     index = 0
#     if num_dialogue > 5 and num_dialogue <= 10:
#         index = 1
#     elif num_dialogue > 10 and num_dialogue <= 15:
#         index = 2
#     elif num_dialogue > 15:
#         index = 3

#     testo_generato = {}
#     i = 1
#     while i<dialogues[index]+1:
#         if len(doctor_lines) >= i:
#             testo_generato[f"doctor_text_{i}"] =  f"{doctor_lines[i-1]}"
#         else:
#             testo_generato[f"doctor_text_{i}"] = "-"

#         if len(patient_lines) >= i:
#             testo_generato[f"patient_text_{i}"] = f"{patient_lines[i-1]}"
#         else:
#             testo_generato[f"patient_text_{i}"] = "-"
#         i+=1

#     import json
#     print(testo_generato)
#     payload = {
#         "test": False,
#         "templateData" : testo_generato,
#         "visibility" : "public",
#         "templateId" : templates[index]
#     }

#     headers = {
#         "accept": "application/json",
#         "content-type": "application/json",
#         "Authorization": "6cc9b1beb23970332eabf466797bc682"
#     }

#     url = "https://api.synthesia.io/v2/videos/fromTemplate"

#     print("--- Payload Generato ---")
#     print(json.dumps(payload, indent=4)) # json.dumps per una stampa leggibile

#     print("\n--- Headers Generati ---")
#     print(json.dumps(headers, indent=4))
#     response = requests.post(url, json=payload, headers=headers)
#     data = json.loads(response.text)
#     print(data)
#     if not data["id"] is None:
#         return data["id"]



def info_video(id, timestamp):
    

    url = f"https://api.synthesia.io/v2/videos/{id}"

    headers = {
    "accept": "application/json",
    "Authorization": "6cc9b1beb23970332eabf466797bc682"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = json.loads(response.text)
        print(data)
        if data["status"] == "complete":
            download_video(data["download"], timestamp)
            return True
        else:
            return False
    else:
        return False

import sys

def download_video(download_url, timestamp):
    headers = {
    "accept": "application/json",
    "Authorization": "6cc9b1beb23970332eabf466797bc682"
    }
    response = requests.get(download_url, headers=headers, stream=True)
    response.raise_for_status()
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
    """Genera un file audio dal testo usando la voce specificata."""
    try:
        data = stream_elements.requestTTS(text, voice.value)
        with open(filename, '+wb') as file:
            file.write(data)
        return filename
    except Exception as e:
        print(f"Errore durante la generazione del parlato per '{text[:30]}...': {e}")
        print("Assicurati che la libreria pyt2s sia configurata correttamente e che ci sia connessione a internet.")
        raise

def create_talking_avatar_clip(audio_path, img_array_open, img_closed, frame_rate_s):
    """
    Crea un video clip di un avatar che parla, sincronizzato con un file audio.
    L'avatar alterna immagini di bocca aperta (selezionate casualmente da img_array_open)
    quando c'è suono, e mostra img_closed quando c'è silenzio.
    """
    try:
        y, sr = librosa.load(audio_path, sr=None) 
    except Exception as e:
        print(f"Errore durante il caricamento di {audio_path} con librosa: {e}")
        raise

    audio_clip_obj = AudioFileClip(audio_path)
    duration = audio_clip_obj.duration

    if duration <= (1 / frame_rate_s):
        min_duration = 1 / frame_rate_s
        print(f"  Avviso: Durata audio in create_talking_avatar_clip ({audio_path}) è minima o zero ({duration:.3f}s). Creo un singolo frame statico di {min_duration:.3f}s.")
        clip_frame = ImageClip(img_closed).with_duration(min_duration)
        try:
            video_segment = clip_frame.with_audio(audio_clip_obj)
        except Exception:
            video_segment = clip_frame
        return video_segment

    frame_length_librosa = 2048
    hop_length_librosa = 512
    rms = librosa.feature.rms(y=y, frame_length=frame_length_librosa, hop_length=hop_length_librosa)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length_librosa)
    
    video_frames = []
    current_time = 0
    threshold_rms = 0.01
    
    mouth_change_interval = 0.1  
    last_mouth_change_time = 0
    current_mouth_image = img_closed
    
    while current_time < duration:
        rms_index = np.argmin(np.abs(times - current_time))
        rms_index = min(rms_index, len(rms) - 1)
        
        is_speaking_now = rms[rms_index] > threshold_rms
        
        if current_time - last_mouth_change_time >= mouth_change_interval:
            if is_speaking_now:
                current_mouth_image = random.choice(img_array_open)
            else:
                current_mouth_image = img_closed
            last_mouth_change_time = current_time

        clip_frame = ImageClip(current_mouth_image).with_duration(1 / frame_rate_s)
        video_frames.append(clip_frame)
        current_time += 1 / frame_rate_s

    if not video_frames: # Assicura che ci sia almeno un frame se la durata era appena sopra la soglia
        video_frames.append(ImageClip(img_closed).with_duration(duration))

    video_segment = concatenate_videoclips(video_frames, method="chain").with_audio(audio_clip_obj)
    return video_segment

# --- 3. Funzione per parsare l'input della conversazione ---
def parse_conversation_input(input_string):
    """
    Parsa una stringa di input nel formato "SPEAKER:text\nSPEAKER:text"
    e restituisce una lista di dizionari.
    """
    parsed_conversation = []
    lines = input_string.strip().split('\n')
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        if ':' not in line:
            print(f"Errore nella riga {line_num + 1}: '{line}'. Formato non valido. Deve essere 'SPEAKER:text'.")
            return None # Restituisce None per indicare un errore di parsing
        
        parts = line.split(':', 1) # Splitto solo al primo ':'
        speaker_raw = parts[0].strip().upper() # Rimuovi spazi e metti in maiuscolo
        text = parts[1].strip()

        speaker_map = {
            "PATIENT": "Paziente",
            "DOCTOR": "Dottore"
        }
        speaker_name = speaker_map.get(speaker_raw, speaker_raw) # Usa il nome mappato o quello grezzo

        parsed_conversation.append({"speaker": speaker_name, "text": text})
            
    return parsed_conversation

# --- 4. Definisci le risorse degli avatar (voci e immagini) ---
FRAME_RATE = 30  # Aumentato per maggiore fluidità
TARGET_HEIGHT = 720  # HD (720p)



# --- 5. Funzione principale per l'elaborazione della conversazione ---
def process_conversation_and_create_video(conversation_data, folder, female):
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

    # Definizione dei percorsi delle immagini
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
        "Paziente": {
            "voice": patient_voice,
            "open_images": [IMG_PATIENT_OPEN_1, IMG_PATIENT_OPEN_2, IMG_PATIENT_OPEN_3],
            "closed_image": IMG_PATIENT_CLOSED
        },
        "Dottore": {
            "voice": stream_elements.Voice.Brian,
            "open_images": [IMG_DOCTOR_OPEN_1, IMG_DOCTOR_OPEN_2, IMG_DOCTOR_OPEN_3], 
            "closed_image": IMG_DOCTOR_CLOSED
        }
    }

    print("Inizio elaborazione conversazione...")
    for i, turn in enumerate(conversation_data):
        speaker = turn["speaker"]
        text = turn["text"]
        
        if speaker not in SPEAKER_RESOURCES:
            print(f"Avviso: Speaker '{speaker}' non riconosciuto. Salto questo turno.")
            continue
        
        voice = SPEAKER_RESOURCES[speaker]["voice"]
        open_images = SPEAKER_RESOURCES[speaker]["open_images"]
        closed_image = SPEAKER_RESOURCES[speaker]["closed_image"]

        print(f"Turno {i+1}: {speaker} dice '{text[:50]}...'") # Aumentato limite anteprima
        
        raw_audio_filename = f"temp_audio_turn_{i}_raw.mp3"
        trimmed_audio_filename = f"temp_audio_turn_{i}_trimmed.wav"
        audio_for_animation_path = None
        turn_duration = 0

        try:
            # 1. Genera il parlato grezzo
            generate_speech(text, voice, raw_audio_filename)
            temp_audio_files.append(raw_audio_filename)

            # 2. Carica l'audio grezzo con Librosa
            y_raw, sr = librosa.load(raw_audio_filename, sr=None)

            # 3. Trimma i silenzi
            y_trimmed, index = librosa.effects.trim(y_raw, top_db=25)

            print(f"  Durata audio grezzo: {len(y_raw)/sr:.2f}s")
            if len(y_trimmed) > 0:
                print(f"  Durata audio trimmato: {len(y_trimmed)/sr:.2f}s")
            else:
                print("  Audio trimmato è vuoto.")

            if len(y_trimmed) == 0:
                print(f"  Avviso: L'audio per il turno {i+1} ('{text[:20]}...') è risultato completamente silenzioso dopo il trimming. Uso l'audio originale.")
                audio_for_animation_path = raw_audio_filename
                with AudioFileClip(raw_audio_filename) as temp_raw_clip:
                     turn_duration = temp_raw_clip.duration
            else:
                # 4. Salva l'audio trimmato in un file .wav
                sf.write(trimmed_audio_filename, y_trimmed, sr)
                temp_audio_files.append(trimmed_audio_filename)
                audio_for_animation_path = trimmed_audio_filename
                with AudioFileClip(trimmed_audio_filename) as temp_trimmed_clip:
                    turn_duration = temp_trimmed_clip.duration
            
            if turn_duration <= 0:
                print(f"  Avviso: Durata audio per il turno {i+1} è <= 0. Imposto a 0.1s.")
                turn_duration = 0.1

        except Exception as e:
            print(f"Impossibile generare, caricare o trimmare l'audio per il turno {i+1}. Salto questo turno. Errore: {e}")
            if os.path.exists(raw_audio_filename) and raw_audio_filename not in temp_audio_files:
                 temp_audio_files.append(raw_audio_filename)
            if os.path.exists(trimmed_audio_filename) and trimmed_audio_filename not in temp_audio_files:
                 temp_audio_files.append(trimmed_audio_filename)
            continue

        print(f"  Creazione clip parlante per {speaker} (durata trimmata: {turn_duration:.2f}s)")
        current_scene = create_talking_avatar_clip(audio_for_animation_path, open_images, closed_image, FRAME_RATE)
        
        current_scene_resized = current_scene.resized(height=TARGET_HEIGHT)
        all_scene_clips.append(current_scene_resized)

    # --- 6. Combina tutte le scene e scrivi il video finale ---
    if not all_scene_clips:
        print("Nessuna scena creata. Uscita.")
    else:
        print("Combinazione di tutte le scene...")
        final_video = concatenate_videoclips(all_scene_clips, method="chain")
        
        output_filename = f"./backend/output/saves/{folder}/videoT.mp4"
        print(f"Scrittura del video finale su {output_filename}...")
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
            print(f"Video finale salvato come {output_filename}")
        except Exception as e:
            print(f"Errore durante la scrittura del video finale: {e}")
            print("Potrebbe essere necessario installare ffmpeg o specificare il percorso corretto.")

        # Pulizia delle risorse video
        if 'final_video' in locals() and final_video is not None:
            final_video.close()
        for scene_clip in all_scene_clips:
            scene_clip.close()

    # --- 7. Pulisci i file audio temporanei ---
    print("Pulizia dei file audio temporanei...")
    for f_path in temp_audio_files:
        if os.path.exists(f_path):
            try:
                os.remove(f_path)
                print(f"  Rimosso: {f_path}")
            except Exception as e:
                print(f"  Errore durante la rimozione di {f_path}: {e}")


def handle_video(conversation, timestamp, female):

    parsed_conversation = parse_conversation_input(conversation)
    request_video(conversation, timestamp)
    if parsed_conversation:
        process_conversation_and_create_video(parsed_conversation, timestamp, female)
    else:
        print("Impossibile procedere a causa di un errore nel parsing dell'input della conversazione.")
