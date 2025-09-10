import tkinter as tk
from tkinter import filedialog
import numpy as np
import sounddevice as sd
import threading
import json
import time
import re
# Sampling rate
SAMPLE_RATE = 44100  

# Global parameters for waveform
wave_amplitude = 0.25
decay_rate = 0.5
note_duration = 10.0
release_fade = 0.1  # seconds for fade out after release
note_to_button = {}

# Octave range
min_octave = 3
num_octaves = 4

# Define all keys for chords (A3 to A4)
chord_types = ["major", "minor"]
chord_keys = ["A3", "A#3", "B3", "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4"]
chord_options = [f"{key} {t}" for key in chord_keys for t in chord_types]

# --- Generate note frequency and waveform ---
def note_freq(note):
    A4 = 440.0
    note_map = {'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4,
                'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2}
    name = note[:-1]
    octave = int(note[-1])
    n = note_map[name] + 12 * (octave - 4)
    return A4 * (2 ** (n / 12.0))

def note_wave(note, duration=None, decay=None, amplitude=None):
    global wave_amplitude, decay_rate, note_duration
    if duration is None:
        duration = note_duration
    if decay is None:
        decay = decay_rate
    if amplitude is None:
        amplitude = wave_amplitude
    f = note_freq(note)
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = amplitude * np.sin(2 * np.pi * f * t) * np.exp(-decay * t)

    # Short fade-in and fade-out at edges
    fade_len = int(0.005 * SAMPLE_RATE)  # 5 ms
    if len(wave) > 2 * fade_len:
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)
        wave[:fade_len] *= fade_in
        wave[-fade_len:] *= fade_out
    return wave

# --- Audio handling ---
active_notes = {}
lock = threading.Lock()
active_chords = {}
chord_lock = threading.Lock()

playing_score = False

def audio_callback(outdata, frames, time_info, status):
    buffer = np.zeros(frames)
    with lock:
        to_remove = []
        for note, wave in active_notes.items():
            length = min(len(wave), frames)
            buffer[:length] += wave[:length]
            active_notes[note] = wave[frames:]
            if len(active_notes[note]) == 0:
                to_remove.append(note)
        for note in to_remove:
            del active_notes[note]
    outdata[:] = buffer.reshape(-1,1)

stream = sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, callback=audio_callback)
stream.start()

def play(note):
    wave = note_wave(note)
    with lock:
        active_notes[note] = wave
    if note in note_to_button:
        btn = note_to_button[note]
        btn.config(bg="green")  # change color when pressed

def stop(note):
    global release_fade
    with lock:
        if note in active_notes:
            wave = active_notes[note]
            fade_length = int(SAMPLE_RATE * release_fade)
            fade_length = min(fade_length, len(wave))  # <- clamp
            fade_wave = wave[:fade_length] * np.linspace(1,0,fade_length)
            active_notes[note] = fade_wave
    if note in note_to_button:
        btn = note_to_button[note]
        btn.config(bg="white" if 'b' not in note and '#' not in note else "black")



# --- Chord utilities ---
def get_chord_notes(root_note, chord_type):
    note_order = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    name = root_note[:-1]
    octave = int(root_note[-1])
    start_idx = note_order.index(name)
    intervals = [0,4,7] if chord_type=="major" else [0,3,7]
    notes=[]
    for i in intervals:
        idx = (start_idx + i) % 12
        new_octave = octave + ((start_idx+i)//12)
        notes.append(note_order[idx]+str(new_octave))
    return notes

def play_chord(idx):
    selection = chord_dropdowns[idx].get()
    if not selection:
        return
    root_note, chord_type = selection.split()
    notes = get_chord_notes(root_note, chord_type)
    with chord_lock:
        for note in notes:
            wave = note_wave(note)
            active_notes[note] = wave
        active_chords[idx] = notes
    chord_buttons[idx].config(bg="green")

def stop_chord(idx):
    with chord_lock:
        if idx in active_chords:
            for note in active_chords[idx]:
                stop(note)
            del active_chords[idx]
    chord_buttons[idx].config(bg="SystemButtonFace")

# --- GUI ---
root = tk.Tk()
root.title("Synth Piano")
root.iconbitmap("icon.ico")

white_notes = ["C","D","E","F","G","A","B"]
black_notes = ["C#","D#",None,"F#","G#","A#",None]
white_w, white_h = 40,200
black_w, black_h = 25,120
note_buttons = []

def build_keys():
    global note_buttons, note_to_button
    for btn in note_buttons:
        btn.destroy()
    note_buttons=[]
    note_to_button = {}
    note_index=0
    for octave in range(min_octave, min_octave+num_octaves):
        for wn in white_notes:
            note = wn+str(octave)
            btn = tk.Button(root, text=note, bg="white")
            btn.place(x=note_index*white_w, y=0, width=white_w, height=white_h)
            btn.bind('<ButtonPress-1>', lambda e,n=note: play(n))
            btn.bind('<ButtonRelease-1>', lambda e,n=note: stop(n))
            note_buttons.append(btn)
            note_to_button[note] = btn  # <-- store mapping
            note_index+=1
    note_index=0
    for octave in range(min_octave, min_octave+num_octaves):
        for i,bn in enumerate(black_notes):
            if bn:
                note = bn+str(octave)
                x_offset = note_index*white_w + white_w-(black_w//2)
                btn = tk.Button(root,text=note,bg="black",fg="white")
                btn.place(x=x_offset, y=0, width=black_w, height=black_h)
                btn.bind('<ButtonPress-1>', lambda e,n=note: play(n))
                btn.bind('<ButtonRelease-1>', lambda e,n=note: stop(n))
                note_buttons.append(btn)
                note_to_button[note] = btn  # <-- store mapping
            note_index+=1


freq_label = tk.Label(root,text="")
freq_label.place(x=650,y=10)

def update_frequency_display():
    min_note = white_notes[0]+str(min_octave)
    max_note = white_notes[-1]+str(min_octave+num_octaves-1)
    min_hz = note_freq(min_note)
    max_hz = note_freq(max_note)
    freq_label.config(text=f"Min: {min_note} {min_hz:.1f} Hz - Max: {max_note} {max_hz:.1f} Hz")

def octave_up():
    global min_octave
    if min_octave + num_octaves < 8:
        min_octave += 1
        build_keys()
        update_key_map()
        update_frequency_display()
        print(f"min octave: {min_octave}")

def octave_down():
    global min_octave
    if min_octave > 1:
        min_octave -= 1
        build_keys()
        update_key_map()
        update_frequency_display()
        print(f"min octave: {min_octave}")


# --- Key mapping ---
# Base key map for octave 0
base_key_map = {
    "a":"A2","s":"B2","d":"C3","f":"D3","g":"E3","h":"F3","j":"G3",
    "k":"A3","l":"B3","ö":"C4","ä":"D4","#":"E4",
    "w":"A#2","r":"C#3","t":"D#3","u":"F#3","i":"G#3","o":"A#3","ü":"C#4","+":"D#4"
}


key_map = {
    "a":"A2","s":"B2","d":"C3","f":"D3","g":"E3","h":"F3","j":"G3",
    "k":"A3","l":"B3","ö":"C4","ä":"D4","#":"E4",
    "w":"A#2","r":"C#3","t":"D#3","u":"F#3","i":"G#3","o":"A#3","ü":"C#4","+":"D#4"
}

def update_key_map():
    global key_map
    global min_octave

    shift = min_octave - 2  # 3 means no change
    new_map = {}

    for key, note in base_key_map.items():
        # Split note into letters and octave using regex
        match = re.match(r"([A-G]#?)(\d+)", note)
        if match:
            letter, octave_str = match.groups()
            new_octave = int(octave_str) + shift
            new_map[key] = f"{letter}{new_octave}"
        else:
            # Fallback: just copy the note if it doesn't match expected format
            new_map[key] = note

    key_map = new_map



pressed_keys = set()
def on_key_press(event):
    key = event.char
    if key in key_map and key not in pressed_keys:
        play(key_map[key])
        pressed_keys.add(key)

def on_key_release(event):
    key = event.char
    if key in key_map and key in pressed_keys:
        stop(key_map[key])
        pressed_keys.remove(key)

root.bind('<KeyPress>', on_key_press, add='+')
root.bind('<KeyRelease>', on_key_release, add='+')

# --- Chord keybinds ---
chord_keybinds = ["<","y","x","c","v","b","n","m",",",".","-"]
pressed_chord_keys = set()

def on_chord_key_press(event):
    key = event.char.lower()
    if key in chord_keybinds and key not in pressed_chord_keys:
        idx = chord_keybinds.index(key)
        play_chord(idx)
        pressed_chord_keys.add(key)

def on_chord_key_release(event):
    key = event.char.lower()
    if key in chord_keybinds and key in pressed_chord_keys:
        idx = chord_keybinds.index(key)
        stop_chord(idx)
        pressed_chord_keys.remove(key)

root.bind('<KeyPress>', on_chord_key_press, add='+')
root.bind('<KeyRelease>', on_chord_key_release, add='+')

# --- Sliders ---
def update_amplitude(val): global wave_amplitude; wave_amplitude=float(val)
def update_decay(val): global decay_rate; decay_rate=float(val)
def update_duration(val): global note_duration; note_duration=float(val)
def update_release(val): global release_fade; release_fade=float(val)

amp_slider = tk.Scale(root,label="Amplitude",from_=0.0,to=1.0,resolution=0.01,orient='horizontal',command=update_amplitude)
amp_slider.set(wave_amplitude); amp_slider.place(x=10,y=260,width=150)
decay_slider = tk.Scale(root,label="Decay",from_=0.01,to=1.0,resolution=0.01,orient='horizontal',command=update_decay)
decay_slider.set(decay_rate); decay_slider.place(x=170,y=260,width=150)
dur_slider = tk.Scale(root,label="Note Duration",from_=1,to=20,resolution=0.5,orient='horizontal',command=update_duration)
dur_slider.set(note_duration); dur_slider.place(x=330,y=260,width=150)
release_slider = tk.Scale(root,label="Release Fade",from_=0.1,to=5.0,resolution=0.1,orient='horizontal',command=update_release)
release_slider.set(release_fade); release_slider.place(x=490,y=260,width=150)

# --- Score ---
current_file='score.json'
def load_file():
    global current_file
    file_path = filedialog.askopenfilename(filetypes=[('JSON files','*.json')])
    if file_path:
        current_file=file_path

def play_score(file_path=current_file):
    global playing_score
    with open(file_path,'r') as f:
        sheet=json.load(f)
    playing_score=True
    for item in sheet:
        if not playing_score:
            break
        notes = item.get('notes') or [item.get('note')]
        duration = item.get('duration', 0.5)
        for n in notes:
            if n != "rest":  # skip rests
                play(n)
        time.sleep(duration)
        for n in notes:
            if n != "rest":
                stop(n)

    playing_score=False

def stop_score(): global playing_score; playing_score=False

# --- Buttons ---
load_btn = tk.Button(root,text="Load JSON",command=load_file)
load_btn.place(x=10,y=220,width=100,height=30)
play_btn = tk.Button(root,text="Play Score",command=lambda: threading.Thread(target=play_score).start())
play_btn.place(x=120,y=220,width=100,height=30)
stop_btn = tk.Button(root,text="Stop Score",command=stop_score)
stop_btn.place(x=230,y=220,width=100,height=30)
up_btn = tk.Button(root,text="Octave +",command=octave_up)
up_btn.place(x=340,y=220,width=100,height=30)
down_btn = tk.Button(root,text="Octave -",command=octave_down)
down_btn.place(x=450,y=220,width=100,height=30)
freq_label = tk.Label(root,text=""); freq_label.place(x=560,y=220,width=300,height=30)

# --- Chord buttons and dropdowns ---
chord_buttons = []
chord_dropdowns = []

for i,key in enumerate(chord_keybinds):
    # Button
    btn = tk.Button(root,text=key)
    btn.place(x=10+i*100,y=340,width=90,height=30)
    btn.bind('<ButtonPress-1>', lambda e,i=i: play_chord(i))
    btn.bind('<ButtonRelease-1>', lambda e,i=i: stop_chord(i))
    chord_buttons.append(btn)

    # Dropdown
    var = tk.StringVar(root)
    var.set(chord_options[i % len(chord_options)])
    dropdown = tk.OptionMenu(root,var,*chord_options)
    dropdown.place(x=10+i*100,y=380,width=90,height=30)
    chord_dropdowns.append(var)

# --- Build initial piano keys ---
build_keys()
update_key_map()
update_frequency_display()

# --- Window size ---
root.geometry(f"{white_w*len(white_notes)*num_octaves+1}x{white_h+250}")
root.mainloop()
