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
    "Generate a commit message in English following the Conventional Commits specification.\n"
    "Rules:\n"
    "- Format: <type>(<optional scope>): <description>\n"
    "- Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert\n"
    "- Write the message in English\n"
    "- Description must be in imperative mood (e.g., 'add' not 'added' or 'adds')\n"
    "- Keep the first line under 50 characters, max 72\n"
    "- Do NOT end the description with a period\n"
    "- Use lowercase for the description\n"
    "- Only output the commit message, nothing else\n\n"
    "Changes:\n\n"
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

def request_commit_message(url: str, headers: dict, diff: str, model: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert at writing concise, clear git commit messages in English following Conventional Commits."},
            {"role": "user", "content": f"{DEFAULT_PROMPT}{diff}"}
        ],
        "temperature": 0.2
    }
    response = requests.post(url, headers=headers, json=payload, timeout=40)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content'].strip().replace('"', '')

def call_llm(diff: str) -> str:
    host = get_config_value("LLM_HOST")
    primary_model = get_config_value("MODEL_NAME")
    fallback_model = get_config_value("FALLBACK_MODEL")
    key = get_config_value("COMMIT_API_KEY")

    if not all([host, primary_model, key]):
        print("❌ Faltan configuraciones. Ejecuta git-commit-ai --config o revisa tu .env")
        sys.exit(1)

    url = f"{host}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    try:
        return request_commit_message(url, headers, diff, primary_model)
    except Exception as primary_error:
        if fallback_model:
            try:
                return request_commit_message(url, headers, diff, fallback_model)
            except Exception as fallback_error:
                print(
                    "❌ Both primary and fallback model attempts failed. "
                    f"Primary ({primary_model}): {primary_error} | "
                    f"Fallback ({fallback_model}): {fallback_error}"
                )
                sys.exit(1)
        print(f"❌ Error LLM: {primary_error}")
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
