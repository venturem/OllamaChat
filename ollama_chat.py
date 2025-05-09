
from nicegui import ui, run
from time import sleep
import requests
import sqlite3
import re
from datetime import datetime


DEFAULT_CHAT_START_MSG = "Hello AI - create me a python program for Fibbonacci series"

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
    print(f"Loaded : {messages}")
    conn.close()
    return messages

import re

def contains_markdown(text: str) -> bool:
    markdown_patterns = [
        r'^#{1,6} ',                  # headings
        r'\*\*(.*?)\*\*',             # bold
        r'_(.*?)_',                   # italic
        r'`{1,3}[^`]+`{1,3}',         # inline/code blocks
        r'^\s*[-*+] ',                # unordered lists
        r'^\s*\d+\.\s',               # ordered lists
        r'\[.*?\]\(.*?\)',            # links
        r'!\[.*?\]\(.*?\)',           # images
    ]
    return any(re.search(pattern, text, re.MULTILINE) for pattern in markdown_patterns)



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

models_list = get_available_models()
print(f" Models Count : {len(models_list)}")
if (len(models_list) == 0):
    print("There are no models to be found...")
    ui.notify("Exiting..")
else:
    selected_model = models_list[0]
selected_model='qwen3:0.6b'

message_stack=[{'role': 'user', 'content': 'input_text'}]

# === UI Setup ===
init_db()



async def process_message(model_name, chat_input):
    global row1, chat_column, message_stack
    input_text = chat_input.value
    if (len(input_text) == 0) : return
    print(f"Input is {input_text}")
    message_stack.append({'role': 'user', 'content': input_text})
    save_message('user',input_text)

    with chat_column:
        ui.chat_message(input_text, sent=False, avatar="https://robohash.org/human")
        placeholder_chat = ui.chat_message("Thinking ...", sent=True, avatar="https://robohash.org/chatbot").classes('animate-pulse text-gray-500 italic')

    payload = {
        'model': model_name,
        'messages': message_stack + [{'role': 'user', 'content': input_text}],
        'stream': False
    }

    output_text=''
    try:
        output_text = await get_model_response(payload)
        # output_text = " ```##Markdown``` "        
    except Exception as e:
        print(f"Something went wrong here... : {e}" )
        ui.notify("There was an error in invoking ollaama model")
    print(f"::: Response is {output_text}")

    chat_column.remove(placeholder_chat)
    with chat_column:
        if (contains_markdown(output_text)): 
            with ui.row().classes('bg-stone-200 border-stone-600 w-full'):
                ui.chat_message("Here is my answer...", sent=True, avatar="https://robohash.org/chatbot").classes(' bg-gray-200 right-full')
                ui.markdown(output_text).classes('accent-amber-950 border-2 bg-gray-200') 
        else: ui.chat_message(output_text, sent=True, avatar="https://robohash.org/chatbot")
    save_message('assistant',output_text)

    print(f"Messages : {message_stack}") 

async def get_model_response(payload):
    URL=f'{OLLAMA_URL}/api/chat'
    # response = requests.post(URL, json=payload)
    response = await run.io_bound(requests.post, URL, json=payload, timeout=300)
    response.raise_for_status()
    data = response.json()
    output_text = data.get('message', {}).get('content', '[No response]')
    # Think tags to be removed
    think_contents = re.findall(r'<think>(.*?)</think>', output_text, flags=re.DOTALL)
    print(f"AI was thinking : {think_contents}" )
    # Remove all think sections from text
    cleaned_text = re.sub(r'<think>.*?</think>', '', output_text, flags=re.DOTALL)
    return cleaned_text   

def set_model(value):
    global selected_model
    selected_model = value.value
    print(f'Selected: {selected_model}')

# === Header ===
with ui.header().classes('bg-blue-600 text-white'):
    ui.button(icon='menu', on_click=lambda: left_drawer.toggle()).props('flat color=white')
    ui.label('Local Ollama Chat').classes('text-xl font-bold ml-4')

# === Blank Left Drawer ===
left_drawer = ui.left_drawer(value=100).classes(' w-full bg-amber-500 border ')
with left_drawer:
    with ui.card(align_items='end').classes('w-full'):
        ui.button("Hello", on_click=lambda: ui.notify('Hi!', position='center', close_button='OK')).classes('w-full')

# === Footer ===
with ui.footer().style('position: static').classes('bg-blue-600 text-white text-center'):
    ui.label('© 2025 Local Ollama Chat')

chat_area = None
labels=[]

message_stack = [ {'role': m['role'], 'content': m['content']} for m in load_history() ]

# === Main Layout ===
with ui.column().classes('bg-blue-200 w-full h-screen p-0 m-0 flex-auto'):

    row1 = ui.row().classes('basis-1/5 bg-green-200 w-full p-10')
    with row1:
        chat_column = ui.column().classes('w-full')

    row2 = ui.row(align_items=['stretch','end']).classes('flex-grow bg-amber-400 w-full p-2.5 ')
    with row2:
        
        chat_input = ui.textarea(label='Ask Query', placeholder='Type your question here', value=DEFAULT_CHAT_START_MSG).classes('w-full bg-blue-100 p-2.5 border-blue-600 border-2 ')
        with ui.button_group().classes('w-full'):
            ui.button('Chat', on_click=lambda: process_message(selected_model, chat_input)).classes('bg-blue-500 ml-2 w-1/3 max-h-20 ')
            select1 = ui.select(models_list, value=selected_model, on_change=lambda e: set_model(e)  ).classes('ml-10 bg-green-500 w-1/2 max-h-20')




# === Run App ===
ui.run(title='NiceGUI Chat Layout')
# left_drawer.toggle()
# left_drawer.toggle()
