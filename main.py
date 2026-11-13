import flet as ft
from flet_audio import Audio
from flet_audio_recorder import AudioRecorder, AudioEncoder
from google import genai
from google.genai import types
from gtts import gTTS
import os
import tempfile
import time

API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY)
conversation_historique = []

def texte_vers_audio(texte):
    tts = gTTS(text=texte, lang='fr', slow=False)
    fichier = os.path.join(tempfile.gettempdir(), f"zenith_{int(time.time())}.mp3")
    tts.save(fichier)
    return fichier

def envoyer_a_gemini(fichier_audio_path, page):
    try:
        page.status_text.value = "🧠 ZENITH réfléchit..."
        page.update()
        with open(fichier_audio_path, "rb") as f:
            audio_data = f.read()
        conversation_historique.append(
            types.Content(role="user", parts=[
                types.Part.from_text(text="Réponds en français, clair et concis."),
                types.Part.from_bytes(data=audio_data, mime_type="audio/mp4")
            ])
        )
        reponse = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=conversation_historique
        )
        texte_reponse = reponse.text
        conversation_historique.append(types.Content(role="model", parts=[types.Part.from_text(text=texte_reponse)]))
        page.chat.controls.append(ft.Text("🎤 Vous : [Message vocal]", color=ft.Colors.GREEN_300))
        page.chat.controls.append(ft.Text(f"🤖 ZENITH : {texte_reponse}", color=ft.Colors.BLUE_400))
        audio_file = texte_vers_audio(texte_reponse)
        page.audio_player.src = audio_file
        page.audio_player.play()
        page.status_text.value = "🎤 Prêt — appuie pour parler"
    except Exception as e:
        page.status_text.value = f"❌ Erreur : {str(e)[:40]}..."
    page.update()

def main(page: ft.Page):
    page.title = "ZENITH"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15
    page.spacing = 20
    page.status_text = ft.Text("🎤 Prêt — appuie pour parler", color=ft.Colors.GREEN_400)
    page.chat = ft.ListView(expand=True, spacing=10, auto_scroll=True, height=350)
    page.audio_player = Audio(src="", autoplay=False)
    page.overlay.append(page.audio_player)
    recorder = AudioRecorder(audio_encoder=AudioEncoder.AAC)
    page.overlay.append(recorder)
    is_recording = False
    chemin = os.path.join(tempfile.gettempdir(), "enregistrement.m4a")
    def enregistrer(e):
        nonlocal is_recording
        if not is_recording:
            if recorder.has_permission():
                recorder.start(output_path=chemin)
                page.status_text.value = "🔴 Enregistrement..."
                page.mic_button.bgcolor = ft.Colors.RED_600
                is_recording = True
            else:
                page.status_text.value = "❌ Autorise le micro"
        else:
            fichier = recorder.stop()
            page.status_text.value = "⏳ Envoi..."
            page.mic_button.bgcolor = ft.Colors.BLUE_GREY_700
            is_recording = False
            page.update()
            if fichier and os.path.exists(fichier):
                envoyer_a_gemini(fichier, page)
        page.update()
    page.mic_button = ft.ElevatedButton(
        content=ft.Icon(ft.Icons.MIC, size=40),
        on_click=enregistrer,
        style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=25, bgcolor=ft.Colors.BLUE_GREY_700)
    )
    page.add(
        ft.Text("🤖 ZENITH", size=26, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        page.status_text,
        ft.Container(page.chat, border=ft.border.all(1, ft.Colors.GREY_700), border_radius=10, padding=10),
        ft.Container(page.mic_button, alignment=ft.alignment.center, padding=15)
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
