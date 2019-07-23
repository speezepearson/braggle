import json
import shlex
import subprocess
from pathlib import Path

LOGFILE = Path('.daemon.log')
quoted_logfile = shlex.quote(str(LOGFILE))

pytest = shlex.quote(subprocess.check_output(['which', 'pytest']).decode('utf8').strip())

TRIGGERS = [
    {
        "name": "compile",
        "expression": [
            "allof",
            ["pcre", "(bridge|tests)/.*\\.py$", "wholename"],
            ["not", ["pcre", "(^|.*/)\\..*", "wholename"]],
        ],
        "append_files": False,
        "command": [
            "bash",
            "-c",
            f"PYTHONPATH=\"$PYTHONPATH:.\" chime-success {pytest} --color=yes >{quoted_logfile} 2>&1"
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
