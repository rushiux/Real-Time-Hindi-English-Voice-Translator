import speech_recognition as sr
from googletrans import Translator
import pyttsx3
from gtts import gTTS
import playsound
import threading
import queue
from datetime import datetime
from rich.console import Console
from rich.table import Table
import os

console = Console()
speak_queue = queue.Queue()
OUTPUT_FILE = "hindi_english_translation.txt"

# Initialize pyttsx3 for English
engine = pyttsx3.init()
engine.setProperty('rate', 150)

# Chat history
chat_history = []

# Worker thread for non-blocking speech
def speak_worker():
    while True:
        lang, text = speak_queue.get()
        if text == "EXIT":
            break
        try:
            if lang == "en":
                engine.say(text)
                engine.runAndWait()
            else:
                tts = gTTS(text=text, lang="hi")
                filename = "temp_hindi.mp3"
                tts.save(filename)
                playsound.playsound(filename)
                os.remove(filename)
        except Exception as e:
            console.print(f"[red]TTS Error:[/red] {e}")
        speak_queue.task_done()

def speak_text(text, lang):
    speak_queue.put((lang, text))

def translate_text(text):
    translator = Translator()
    detected_lang = translator.detect(text).lang
    if detected_lang == "hi":
        translated = translator.translate(text, dest="en")
        return "Hindi → English", translated.text, "en"
    else:
        translated = translator.translate(text, dest="hi")
        return "English → Hindi", translated.text, "hi"

def save_to_file(original, translated, direction):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(f"Direction: {direction}\n")
        f.write(f"Original: {original}\n")
        f.write(f"Translated: {translated}\n")

def display_chat():
    table = Table(title="[bold yellow]Hindi ↔ English Translation History[/bold yellow]", show_lines=True)
    table.add_column("Direction", justify="center", style="magenta", width=18)
    table.add_column("Original Speech", justify="center", style="cyan", width=40)
    table.add_column("Translated Text", justify="center", style="green", width=40)

    for entry in chat_history[-10:]:  # Last 10 messages
        table.add_row(entry["direction"], entry["original"], entry["translated"])

    console.clear()
    console.print(table)

def real_time_translation():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    threading.Thread(target=speak_worker, daemon=True).start()

    console.print("[bold green]✅ Real-time Hindi ↔ English Translator (Jarvis Mode)[/bold green]")
    console.print("[yellow]Say 'stop translation' to exit.[/yellow]\n")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

        while True:
            try:
                console.print("[bold blue]Listening...[/bold blue]")
                audio = recognizer.listen(source)

                # Always recognize in English mode for better accuracy
                text = recognizer.recognize_google(audio, language="en-IN")

                if text.lower() == "stop translation":
                    speak_queue.put(("en", "EXIT"))
                    console.print("[bold red]Stopping translation...[/bold red]")
                    break

                # Translate using detected language
                direction, translated_text, lang = translate_text(text)

                # Save to history
                chat_history.append({"direction": direction, "original": text, "translated": translated_text})

                # Show chat in terminal
                display_chat()

                # Speak translation
                speak_text(translated_text, lang)

                # Save to file
                save_to_file(text, translated_text, direction)

            except sr.UnknownValueError:
                console.print("[red]Could not understand audio, try again...[/red]")
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    real_time_translation()
