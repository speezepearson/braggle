import json
import shlex
import subprocess
from pathlib import Path

LOGFILE = Path('.daemon.log')

TRIGGERS = [
    {
        "name": "compile",
        "expression": [
            "allof",
            ["pcre", "src/.*\\.elm$", "wholename"],
            ["not", ["pcre", "(^|.*/)\\..*", "wholename"]],
            ["not", ["pcre", "(^|.*/)elm-stuff/.*", "wholename"]]
        ],
        "append_files": False,
        "command": [
            "bash",
            "-c",
            f"chime-success elm make src/Main.elm >{shlex.quote(str(LOGFILE))} 2>&1"
        ]
    }
]

subprocess.run(['watchman', 'watch', '.'])
for trigger in TRIGGERS:
    subprocess.run(['watchman', '-j',], input=json.dumps(['trigger', '.', trigger]).encode('utf8'))

LOGFILE.open('a').close()
try:
    subprocess.run(['tail', '-f', str(LOGFILE)])
except KeyboardInterrupt:
    print('Keyboard interrupt received. Deactivating watchman triggers...')
    for trigger in TRIGGERS:
        subprocess.run(['watchman', 'trigger-del', '.', trigger['name']])
