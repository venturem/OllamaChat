from nicegui import ui
import requests
import sqlite3
from datetime import datetime
import asyncio

# === SQLite Setup ===
DB_PATH = 'chat_history.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    role TEXT,
                    content TEXT
                )''')
    conn.commit()
    conn.close()

def save_message(role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO messages (timestamp, role, content) VALUES (?, ?, ?)',
              (datetime.now().isoformat(), role, content))
    conn.commit()
    conn.close()

def load_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT role, content FROM messages ORDER BY id ASC')
    messages = c.fetchall()
    conn.close()
    return messages

# === Ollama API Interaction ===
OLLAMA_URL = 'http://localhost:11434'

def get_available_models():
    try:
        response = requests.get(f'{OLLAMA_URL}/api/tags')
        response.raise_for_status()
        data = response.json()
        return [m['name'] for m in data.get('models', [])]
    except Exception as e:
        print('Failed to get models:', e)
        return []

def chat_with_ollama(model, message, history):
    payload = {
        'model': model,
        'messages': history + [{'role': 'user', 'content': message}],
        'stream': False
    }
    response = requests.post(f'{OLLAMA_URL}/api/chat', json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get('message', {}).get('content', '[No response]')

# === UI Setup ===
init_db()
chat_history_ui = ui.column().classes('w-full max-w-2xl mx-auto p-4')

# Get models and set default
model_list = get_available_models()
if not model_list:
    raise RuntimeError("❌ No models found in Ollama. Run `ollama pull <model>` first.")
selected_model = {'name': model_list[0]}

# Model dropdown
with ui.row().classes('justify-center p-2'):
    ui.label('Choose model:')
    ui.select(model_list, value=selected_model['name'],
              on_change=lambda e: selected_model.update({'name': e.value})
              ).classes('w-48')

# Display past history
message_stack = []
for role, content in load_history():
    with chat_history_ui:
        if role == 'user':
            ui.html(f'<b>User:</b> {content}').classes('bg-gray-100 p-3 rounded shadow mb-2 w-full')
        else:
            ui.html(f'<b>Assistant:</b> {content}').classes('bg-blue-100 p-3 rounded shadow mb-2 w-full')
    message_stack.append({'role': role, 'content': content})

# Input & Button
user_input = ui.input(placeholder='Type your message...').classes('w-full')
ui.button('Send', on_click=lambda: send_message()).classes('mt-2')

# Async message sending
async def send_message():
    msg = user_input.value.strip()
    if not msg:
        return
    model = selected_model['name']

    with chat_history_ui:
        ui.html(f'<b>User:</b> {msg}').classes('bg-gray-100 p-3 rounded shadow mb-2 w-full')
    save_message('user', msg)
    message_stack.append({'role': 'user', 'content': msg})
    user_input.value = ''

    spinner = ui.spinner(size='lg').classes('mt-4')
    try:
        response = await ui.run_io(lambda: chat_with_ollama(model, msg, message_stack))
        with chat_history_ui:
            ui.html(f'<b>Assistant ({model}):</b> {response}').classes('bg-blue-100 p-3 rounded shadow mb-2 w-full')
        save_message('assistant', response)
        message_stack.append({'role': 'assistant', 'content': response})
    except Exception as e:
        with chat_history_ui:
            ui.html(f'<b>Error:</b> {str(e)}').classes('bg-red-100 p-3 rounded shadow mb-2 w-full')
    finally:
        spinner.visible = False

# Start the app
ui.run(title='Ollama Chat')
