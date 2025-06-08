# DH_AIDoctorNotes

AIDoctorNotes is an end-to-end AI-driven system that simulates and captures doctor-patient conversations, transcribes the dialogue, generates clinical notes, and produces an animated video that simulates the conversation.

![Screenshot 2025-06-08 alle 18 00 07](https://github.com/user-attachments/assets/2f62ebf6-466a-4ab4-b431-433acfb30cbe)


Project Overview
This project automates the documentation of doctor-patient interactions through four main phases:

Audio Capture
Captures real-time conversation using PyAudio, storing it as a .wav file with timestamp-based naming. Audio recording is handled in a separate thread to ensure responsiveness.

Transcription & Diarization
Uses the AssemblyAI API to transcribe speech and perform speaker diarization, identifying DOCTOR and PATIENT roles. Gender classification is applied using librosa for avatar selection.

Dialogue Analysis & Note Generation
Refined text and clinical summaries are generated using LLaMA 3 via the Together API. The LLM corrects transcription errors, assigns speaker roles, and extracts structured medical notes from the dialogue.

Video Rendering & Report Output

Produces two video versions:

A placeholder animation with cartoon avatars via MoviePy, rendered instantly

A high-fidelity AI avatar video rendered asynchronously via the Synthesia API

Clinical notes are compiled into a styled HTML template and exported as a PDF.

HOW TO RUN

It will require the installation of some python libraries. 
To run the application just execute ./frontend/gui.py
