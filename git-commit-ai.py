#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv, set_key

# Intentar cargar variables desde un archivo .env en el directorio actual
load_dotenv()

CONFIG_FILE_JSON = Path.home() / ".git-commit-ai.json"
ENV_FILE = Path(".env")

DEFAULT_PROMPT = (
    "Genera un mensaje de commit siguiendo la convención de 'Conventional Commits'. "
    "Usa el formato: <tipo>: <descripción corta en minúsculas>.\n"
    "Cambios realizados:\n\n"
)

def get_config_value(key: str) -> Optional[str]:
    # 1. Prioridad: Variable de entorno (o .env cargado)
    if os.getenv(key):
        return os.getenv(key)
    
    # 2. Secundaria: Archivo JSON global
    if CONFIG_FILE_JSON.exists():
        with open(CONFIG_FILE_JSON, "r") as f:
            config = json.load(f)
            return config.get(key)
    return None

def save_config(host: str, model: str, api_key: str):
    # Si existe un .env, guardamos ahí. Si no, en el JSON global.
    if ENV_FILE.exists():
        set_key(str(ENV_FILE), "LLM_HOST", host)
        set_key(str(ENV_FILE), "MODEL_NAME", model)
        set_key(str(ENV_FILE), "COMMIT_API_KEY", api_key)
        print(f"✅ Configuración actualizada en {ENV_FILE}")
    else:
        config = {
            "LLM_HOST": host.rstrip('/'),
            "MODEL_NAME": model,
            "COMMIT_API_KEY": api_key
        }
        with open(CONFIG_FILE_JSON, "w") as f:
            json.dump(config, f, indent=4)
        print(f"✅ Configuración guardada en {CONFIG_FILE_JSON}")

def get_staged_diff() -> str:
    try:
        diff = subprocess.check_output(["git", "diff", "--cached"], text=True, encoding="utf-8")
        return diff
    except subprocess.CalledProcessError:
        print("❌ Error: No se pudo acceder a Git.")
        sys.exit(1)

def call_llm(diff: str) -> str:
    host = get_config_value("LLM_HOST")
    model = get_config_value("MODEL_NAME")
    key = get_config_value("COMMIT_API_KEY")

    if not all([host, model, key]):
        print("❌ Faltan configuraciones. Ejecuta git-commit-ai --config o revisa tu .env")
        sys.exit(1)

    url = f"{host}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Eres un experto en commits."},
            {"role": "user", "content": f"{DEFAULT_PROMPT}{diff}"}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip().replace('"', '')
    except Exception as e:
        print(f"❌ Error LLM: {e}")
        sys.exit(1)

def main():
    if "--config" in sys.argv:
        host = input("🔗 LLM Host: ")
        model = input("🤖 Model Name: ")
        key = input("🔑 API Key: ")
        save_config(host, model, key)
        return

    diff = get_staged_diff()
    if not diff:
        print("📭 Nada en el stage. Usa 'git add'.")
        return

    print("🤖 Generando mensaje...")
    commit_msg = call_llm(diff)

    print(f"\n📝 Propuesta: {commit_msg}")
    choice = input("\n¿Aceptar, Editar o Cancelar? [a/e/c]: ").lower()

    if choice == 'a':
        subprocess.run(["git", "commit", "-m", commit_msg])
    elif choice == 'e':
        nuevo = input("Mensaje: ")
        if nuevo: subprocess.run(["git", "commit", "-m", nuevo])
    else:
        print("Abortado.")

if __name__ == "__main__":
    main()
