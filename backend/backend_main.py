from handle_rec import stop_recording, remove_noise, transcript_audio, analyze_dialogue, generate_html_report

def handle_output(file_name):
    stop_recording(str(file_name))
    #dialogue = transcript_audio(str(file_name))
    #print(dialogue)
    #conversation, doctor_notes = analyze_dialogue(dialogue)
    doctor_notes = """
    - Reported symptoms: Terrible stomach ache, vomiting, no diarrhea  \n- Duration and severity: Symptoms started last night and are still ongoing, severity is moderate to severe  \n- Possible diagnosis: Food poisoning, possibly related to seafood in the meal cooked by the patient's children, or a gastrointestinal infection  \n- Suggested follow-ups or tests: Stool tests, possibly blood work to check for signs of infection, and a consultation with a specialist if the symptoms persist or worsen."""
    doctor_notes = generate_html_report(doctor_notes)
    return [None, "conversation", doctor_notes]