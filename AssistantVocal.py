# -------------------------------------------------------------- #
#                                                                #
# Projet: Assistant Vocal                                        #
#                                                                #
# Fichier: AssistantVocal.py                                     #
# Auteur: KOIexe                                                 #
# Date: 15/09/2025                                               #
# Python: 3.12.1                                                 #
# Version: 1.00                                                  #
#                                                                #
# Description: Un assistant vocal simple en Python utilisant     #
#              Vosk pour la reconnaissance vocale et edge-tts    #
#              pour la synthèse vocale.                          #
#                                                                #
# -------------------------------------------------------------- #


# --------------------------
#           Debug
# --------------------------

Debug = False  # Mettre à True pour activer les messages de debug et False pour les désactiver


# --------------------------
#          Imports
# --------------------------
from playsound3 import playsound
import edge_tts
import asyncio
import os
import webbrowser as wb
import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
import imageio_ffmpeg as ffmpeg


# --------------------------
#        Constantes
# --------------------------

FFMPEG_PATH = ffmpeg.get_ffmpeg_exe()
MODEL_PATH = "vosk-model-small-fr-0.22"
SAMPLE_RATE = 16000

# Vérification de l'existence du modèle
if not os.path.exists(MODEL_PATH):
    print ("Veuillez télécharger le modèle depuis https://alphacephei.com/vosk/models et le décompresser dans le dossier courant.")
    exit(1)

q = queue.Queue()

if Debug:
    print("Chargement du modèle...")


# --------------------------
#        Variables
# --------------------------

assistant_actif = False
text = ""
commandeID = -1


# --------------------------
#    Verifications FFMPEG
# --------------------------

if not os.path.exists(FFMPEG_PATH):
    print("FFmpeg introuvable via imageio-ffmpeg")
else:
    if Debug:
        print(f"FFmpeg trouvé: {FFMPEG_PATH}")


# --------------------------
#  Initialisation du model
# --------------------------

if Debug:
    print("Chargement du modèle...")

model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, SAMPLE_RATE)    #Initialisation du reconnaisseur

# --------------------------
# Commandes et Dictionnaires
# --------------------------

list_commande = ["stop", "ouvre", "lance", "non"]

dic_programme = {
    "VLC": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
    "fichier": "C:\\Windows\\explorer.exe",
    "wes code": "C:\\Program Files\\Microsoft VS Code\\Code.exe",
    "weiss mode": "C:\\Program Files\\Voicemod V3\\Voicemod.exe",
    "internet": "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",

}

dic_site = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "musique": "https://www.deezer.com/fr/profile/6289050543/loved",
    "dashboard": "http://hommar",
    "les mail": "https://mail.google.com/mail/u/0/#inbox",

}


# --------------------------
#         Fonctions
# --------------------------

async def tts_play(Texte):              # Fonction asynchrone pour la synthèse vocale
    # Suppression du fichier temporaire s'il existe
    if os.path.exists("temp.mp3"):
        os.remove("temp.mp3")

    # Envoi du texte à edge-tts
    communicate = edge_tts.Communicate(
        Texte,
        voice="fr-FR-HenriNeural"
    )
    # Sauvegarde temporaire et lecture du fichier audio
    await communicate.save("temp.mp3")
    playsound("temp.mp3")
    os.remove("temp.mp3")


def dire(Texte):                     # Fonction simplifier pour exécuter la synthèse vocale
    asyncio.run(tts_play(Texte))


def audio_callback(indata, frames, time, status):   # Fonction de rappel pour capturer l'audio
    if status:
        print(status)
    q.put(bytes(indata))


def ecouter():                     # Fonction pour écouter et reconnaître la parole
    global text

    try:
        data = q.get(timeout=2)
    except queue.Empty:
        print("Pas de signale du micro")
        return ""

    if recognizer.AcceptWaveform(data):
        result = recognizer.Result()
        text = json.loads(result)["text"]
        if Debug and text:
            print("Reconnu:", text)
        return text
    return ""


def detectcommande():               # Fonction pour détecter les commandes dans le texte reconnu
    global commandeID, assistant_actif

    commandeID = -1
    for i in list_commande:
        # Diviser le texte en mots
        commande = text.split()
        if i in commande:
            # Trouver l'ID de la commande
            commandeID = list_commande.index(i)
            if Debug:
                print(f'Commande détécter: "{i}" son ID est {commandeID}')
    if commandeID == -1:
        playsound("Pas_compris.mp3")
        assistant_actif = True
        if Debug:
            print(f"Aucune commande trouvé dans {text}, assistant réactivé")
    return commandeID



def executecommande():         # Fonction pour exécuter les commandes détectées
    global text

    if commandeID == 0:       # Commande "stop"
        print("Arret du programe")
        playsound("Au_revoir.mp3")
        # Stoppe le programme
        exit()

    elif commandeID == 1:      # Commande "ouvre"
        for i in dic_site.keys():
            # Chercher le site dans le texte
            site = text.find(i)

            if Debug:
                print(f"Recherche du site: {i} dans le texte")
            if site >= 0:
                # Récupérer l'URL du site
                site = dic_site.get(i)
                try:
                    # Ouvrir le site dans le navigateur par défaut
                    wb.open(site)
                    dire(f"Ouverture de {i}")
                except Exception as e:
                    # Si une erreur survient
                    dire(f"Je n'ai pas pu ouvrir {i} \nproblème rencontré: {e}")

                if Debug:
                    print(f"Ouverture de {site}")

    elif commandeID == 2:       # Commande "lance"
        for i in dic_programme.keys():
            # Chercher le programme dans le texte
            programme = text.find(i)

            if Debug:
                print(f"Recherche du programme: {i} dans le texte")
            if programme >= 0:
                # Récupérer le chemin du programme
                programme = dic_programme.get(i)
                try:
                    # Lancer le programme
                    os.startfile(programme)
                    dire(f"Lancement de {i}")
                except Exception as e:
                    # Si une erreur survient
                    dire(f"Je n'ai pas pu lancer {i} \nproblème rencontré: {e}")

                if Debug:
                    print(f"Lancement de {programme}")

    elif commandeID == 3:       # Commande "non"
        if Debug:
            print("Assistant mis en veille")


# --------------------------
#         Main Loop
# --------------------------

with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype="int16", channels=1, callback=audio_callback):
    # Joue le son Bonjour.mp3 pour signaler le début du programme
    playsound("Bonjour.mp3")

    try:
        while True:
            # Écoute pour détéction
            phrase = ecouter()
            if Debug:
                print("écoute")

            # Détéction de siri ou de cyril pour commancer l'utilisation des commandes
            if "biscotte" in phrase:
                # Active l'utilisation des commandes
                assistant_actif = True
                if Debug:
                    print("Assistant activé")
                # Joue le son Oui.mp3 pour prévenire que les commandes sont activer
                playsound("Oui.mp3")
                continue

            if assistant_actif and phrase:
                # Désactive l'utilisation des commandes pour la prochaine utillisation
                assistant_actif = False
                if Debug:
                    print("Assistant en veille")

                # Détècte et execute la commande de l'utilisateur
                detectcommande()
                executecommande()

    except KeyboardInterrupt:
        # Si L'utilisateur fait Ctrl + C
        print("Fin du programme demandée par l'utilisateur")

