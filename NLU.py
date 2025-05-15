from ASR import transcribe_file
from intent_prototypes import match_intent

def process_audio(file_path: str) -> dict:
    text = transcribe_file(file_path)
    intent = match_intent(text)
    return {
        "text":   text,
        "intent": intent,
        "slots":  {}
    }
