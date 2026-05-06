# Git-Commit-AI 🤖

Git-Commit-AI es una herramienta CLI escrita en Python que automatiza la creación de mensajes de commit semánticos y estandarizados. Analiza los cambios que están en el *stage* (`git add`) y utiliza un modelo de lenguaje (LLM) para generar una descripción precisa siguiendo la convención de [Conventional Commits](https://www.conventionalcommits.org/).

## ✨ Características

- 🧠 **Inteligente:** Analiza el `git diff` real para entender tus cambios.
- 📝 **Estandarizado:** Genera mensajes tipo `<tipo>: <descripción>`.
- ⚙️ **Configurable:** Funciona con cualquier proveedor compatible con la API de OpenAI (OpenAI, Ollama, LM Studio, etc.).
- 🛠 **Interactivo:** Te permite aceptar, editar o cancelar el mensaje propuesto antes de hacer el commit.

## 📋 Requisitos

- **Python 3.12** o superior.
- Git instalado y accesible desde la terminal.
- Acceso a una API de LLM (puede ser local como Ollama o remota como OpenAI/Mistral).

## 🚀 Instalación

1. **Descarga o clona el proyecto:**
   Asegúrate de tener los archivos en tu máquina local.

2. **Crea un entorno virtual (recomendado):**
   ```bash
   python -m venv venv
   # Activar en macOS/Linux:
   source venv/bin/activate
   # Activar en Windows:
   # venv\Scripts\activate
   ```

3. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuración

Antes de usarlo, necesitas configurar la conexión con tu LLM. Tienes dos formas de hacerlo:

### Opción 1: Configuración Interactiva (Recomendada)
Ejecuta el script con el argumento `--config`. Esto guardará tus credenciales en un archivo `.env` local (si existe) o en un archivo de configuración global en tu usuario (`~/.git-commit-ai.json`).

```bash
python git-commit-ai.py --config
```

Te pedirá los siguientes datos:
- **LLM Host**: URL base de la API.
  - Ejemplo Ollama: `http://localhost:11434`
  - Ejemplo OpenAI: `https://api.openai.com`
- **Model Name**: Nombre del modelo a usar.
  - Ejemplos: `llama3`, `mistral`, `gpt-4o`.
- **API Key**: Tu clave de API.
  - Si usas Ollama o un servidor local sin auth, puedes escribir cualquier cosa (ej. `ollama`).

### Opción 2: Archivo `.env` Manual
Crea un archivo `.env` en la raíz del directorio donde está el script con el siguiente contenido:

```ini
LLM_HOST=http://localhost:11434
MODEL_NAME=llama3
FALLBACK_MODEL=llama3.1
COMMIT_API_KEY=ollama
```

`FALLBACK_MODEL` es opcional. Si el modelo principal falla, la herramienta reintenta una vez con este modelo.

## 🛠 Configuración de Acceso Rápido (Alias)

Para no tener que escribir `python /ruta/al/script.py` cada vez, puedes crear un alias en tu terminal:

1. **Obtén la ruta absoluta** de tu script:
   ```bash
   pwd  # Esto te dará la ruta, ej: /Users/tu_usuario/git-commit-ai
   ```

2. **Añade el alias** a tu archivo de configuración (`.zshrc` o `.bashrc`):
   ```bash
   # Abre el archivo (ejemplo con zsh)
   nano ~/.zshrc

   # Añade esta línea al final (ajusta la ruta y el nombre de tu binario python):
   alias git-commit-ai='/Users/tu_usuario/git-commit-ai/venv/bin/python /Users/tu_usuario/git-commit-ai/git-commit-ai.py'
   ```

3. **Recarga la configuración**:
   ```bash
   source ~/.zshrc
   ```

Ahora puedes usar simplemente `git-commit-ai` desde cualquier carpeta que sea un repositorio Git.

## 💻 Uso

El flujo de trabajo es sencillo:

1. **Realiza tus cambios** en el código.
2. **Añade los archivos al *stage*** como harías normalmente:
   ```bash
   git add .
   ```
3. **Ejecuta la herramienta:**
   ```bash
   git-commit-ai
   ```
4. **Interactúa con el asistente:**
   La herramienta analizará los cambios y te mostrará una propuesta. Elige una opción:
   - `a`: **Aceptar** la propuesta y realizar el commit automáticamente.
   - `e`: **Editar** el mensaje manualmente si no te convence del todo.
   - `c`: **Cancelar** la operación.

### Ejemplo de ejecución

```text
$ git add .
$ python git-commit-ai.py

🤖 Generando mensaje...

📝 Propuesta: feat: implementar sistema de login con jwt

¿Aceptar, Editar o Cancelar? [a/e/c]: a
[main 8f3d2a1] feat: implementar sistema de login con jwt
 1 file changed, 45 insertions(+)
```