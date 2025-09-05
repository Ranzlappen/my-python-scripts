# my-python-scripts
# synth piano for personal testing and songwriting/covering purposes
default keybinds are (german keyboard layout) 

```
key_map = {
    "a":"A2","s":"B2","d":"C3","f":"D3","g":"E3","h":"F3","j":"G3",
    "k":"A3","l":"B3","ö":"C4","ä":"D4","#":"E4",
    "w":"A#2","r":"C#3","t":"D#3","u":"F#3","i":"G#3","o":"A#3","ü":"C#4","+":"D#4"
}
```
and 
```
chord_keybinds = ["<","y","x","c","v","b","n","m",",",".","-"]
```

## TODO: better score import/playback logic, currently takes files with the format 
```
[
    {"notes": ["F4", "A4", "C5"], "duration": 1.0},
    {"notes": ["E4", "G4", "B4"], "duration": 1.0},
    {"notes": ["A4", "C5", "E5"], "duration": 1.0},
    {"notes": ["G4", "B4", "D5"], "duration": 1.0},
    {"notes": ["F4", "A4", "C5"], "duration": 1.0},
    {"note": "rest", "duration": 0.5},
    {"notes": ["E4", "G4", "B4"], "duration": 1.0},
    {"note": "rest", "duration": 0.5},
    {"notes": ["A4", "C5", "E5"], "duration": 1.0},
    {"note": "rest", "duration": 0.5},
    {"notes": ["G4", "B4", "D5"], "duration": 1.0},
    {"note": "rest", "duration": 0.5},
    {"notes": ["F4", "A4", "C5"], "duration": 1.0},
    {"note": "rest", "duration": 0.5}
]
```
as score.json

![Screenshot](Screenshot%202025-09-05%20190551.png)
