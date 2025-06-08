from handle_rec import stop_recording, remove_noise, transcript_audio, analyze_dialogue, generate_html_report, save_files
from handle_video import handle_video
import os

def handle_output(file_name):
    stop_recording(str(file_name))
    dialogue, female = transcript_audio(str(file_name))
    conversation, doctor_notes, conv_old = analyze_dialogue(dialogue)
    doctor_notes = generate_html_report(doctor_notes)
    save_files(conversation, doctor_notes, None, str(file_name))
    handle_video(conv_old, file_name, female)
    return [os.path.abspath(f"./backend/output/saves/{file_name}/"), conversation, doctor_notes]