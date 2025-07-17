# DH_AIDoctorNotes

A proof-of-concept application that automates clinical documentation by transforming doctor-patient audio into structured notes, refined transcripts, and video summaries.

![Screenshot 2025-06-08 alle 18 00 07](https://github.com/user-attachments/assets/2f62ebf6-466a-4ab4-b431-433acfb30cbe)


---

## Key Features

* **Direct Audio Recording**: Capture conversations from within the app.
* **AI-Powered Transcription**: Uses **AssemblyAI** for accurate transcription and speaker diarization.
* **Dialogue Analysis**: Leverages **Meta Llama 3** to refine text, assign `DOCTOR`/`PATIENT` roles, and extract clinical insights.
* **Automated Medical Notes**: Generates a structured medical report in PDF format.
* **Dual Video Summaries**: Creates both an instant avatar video and a final photorealistic video that recreates the conversation.
* **Conversation Archive & Export**: Saves all sessions and allows users to download all associated files.

---

## Application Preview

Here is a quick look at the application's user interface.

| Main Interface (Recording)                                 | Conversation Archive                                |
| ---------------------------------------------------------- | --------------------------------------------------- |
| <img width="581" height="737" alt="Screenshot 2025-07-18 alle 00 35 13" src="https://github.com/user-attachments/assets/7327de3c-7614-4160-9422-a6fbcfd87ba1" /> | <img width="577" height="715" alt="Screenshot 2025-07-18 alle 00 35 57" src="https://github.com/user-attachments/assets/4ea14430-528a-41db-8f8a-2bc1be561540" /> |

---

## Project Outputs

The application processes a single audio recording to produce four distinct digital assets, including two types of video.

### 1. Refined Dialogue Transcript

The raw, machine-generated transcript is corrected and clarified by the LLM, with contextual roles assigned.

**Example:**
* **Before (Raw from AssemblyAI):**
    > Speaker A: How are you today
    > Speaker B: I have some jest pain.

* **After (Refined by Llama 3):**
    > **DOCTOR:** "How are you today?"
    > **PATIENT:** "I have some chest pain."

### 2. Structured Clinical Notes (PDF)

Clinically relevant information is extracted and organized into a formal report that is easy to read and download.

<img width="572" height="674" alt="Screenshot 2025-07-18 alle 00 36 52" src="https://github.com/user-attachments/assets/23b5ffaf-6569-4987-82f1-573f1305781f" />

### 3. Instant Avatar Video (Placeholder)

To provide immediate feedback, a simple cartoon-style avatar video is generated instantly using MoviePy while the final version renders.

![ezgif-8973e4a498ab1f](https://github.com/user-attachments/assets/7b127ffa-94b7-49bf-86b7-6aabfab82406)

### 4. Photorealistic Video Summary (Final)

The final output is a high-fidelity video of the conversation, created using Synthesia's realistic talking avatars for a professional and dynamic review.

---

## Tech Stack

* **Backend**: Python
* **AI Services**:
    * **Speech-to-Text**: AssemblyAI
    * **LLM**: Meta Llama 3 (via Together API)
    * **Video Generation**: Synthesia
* **Core Libraries**: `PyAudio`, `librosa`, `MoviePy`

---

## How It Works

1.  **Capture**: The conversation is recorded and saved as a `.wav` file.
2.  **Transcribe**: The audio is sent to **AssemblyAI** for transcription and speaker diarization.
3.  **Analyze**: **Llama 3** refines the transcript, assigns roles, and extracts clinical data.
4.  **Generate**: The final outputs (**PDF notes**, an **instant avatar video**, and a **final photorealistic video**) are created from the processed data.

---

## Getting Started

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/roccopastore/DH_AIDoctorNotes.git](https://github.com/roccopastore/DH_AIDoctorNotes.git)
    cd DH_AIDoctorNotes
    ```

2.  **Install dependencies:**

3.  **Configure API Keys:**
    This projects requires three API KEYS:
    ```env
    ASSEMBLYAI_API_KEY="your_assemblyai_api_key"
    TOGETHER_API_KEY="your_together_ai_api_key"
    SYNTHESIA_API_KEY="your_synthesia_api_key"
    ```

4.  **Run the application:**
    ```sh
    python guy.py
    ```

---

## Author

* **Rocco Pastore** - [roccopastore](https://github.com/roccopastore)
