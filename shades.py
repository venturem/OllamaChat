from nicegui import ui

# Tailwind color families and typical shades
colors = [
    'slate', 'gray', 'zinc', 'neutral', 'stone',
    'red', 'orange', 'amber', 'yellow', 'lime',
    'green', 'emerald', 'teal', 'cyan', 'sky',
    'blue', 'indigo', 'violet', 'purple', 'fuchsia',
    'pink', 'rose'
]

shades = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]

ui.label('Tailwind Background Color Grid').classes('text-2xl m-4 font-bold')

with ui.row().classes('overflow-x-auto'):
    for color in colors:
        with ui.column().classes('min-w-36 border rounded overflow-hidden shadow'):
            ui.label(color.capitalize()).classes('text-center font-semibold p-2 bg-white')
            for shade in shades:
                class_name = f'bg-{color}-{shade}'
                text_color = 'text-black' if shade < 500 else 'text-white'
                ui.label(f'{color}-{shade}').classes(f'{class_name} {text_color} p-2 text-xs text-center')

ui.run(host='127.0.0.1',port=8181)
