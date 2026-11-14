"""One-board installation; retain official pairing/config, no motion tests."""
from pathlib import Path
import hashlib, json, subprocess, sys
from serial.tools import list_ports

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / '待上传_蓝色巴掌2_D2_2026-11-13'
BACKUP = ROOT / '现场备份_2026-11-13_蓝色2_D2_COM17'
PORT = 'COM17'
assert any(p.device == PORT and p.serial_number == '80:F1:B2:1E:B3:6C'
           for p in list_ports.comports()), 'Wrong or missing board'

def remote(*args):
    p = subprocess.run([sys.executable, '-m', 'mpremote', 'connect', PORT,
                        'resume', *args], capture_output=True, timeout=60)
    output = p.stdout.decode('utf-8', 'replace')
    if p.returncode:
        raise RuntimeError(output + p.stderr.decode('utf-8', 'replace'))
    return output

def hashes(paths):
    code = "import uhashlib,ubinascii,ujson\nout={}\n"
    code += 'for p in ' + repr(paths) + ':\n'
    code += " h=uhashlib.sha256()\n f=open('/'+p,'rb')\n while True:\n  b=f.read(1024)\n  if not b: break\n  h.update(b)\n f.close()\n out[p]=ubinascii.hexlify(h.digest()).decode()\n"
    code += "print('HASHJSON:'+ujson.dumps(out))"
    text = remote('exec', code)
    return json.loads(text.split('HASHJSON:')[1].splitlines()[0])

def local_hashes(folder):
    return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob('*') if p.is_file()}

before = local_hashes(BACKUP)
assert hashes(list(before)) == before, 'Backup differs from board; stop'
print('Verified original backup:', len(before), 'files', flush=True)
files = local_hashes(STAGE)
remote('exec', "import os\nif 'drivers' not in os.listdir('/'): os.mkdir('/drivers')")
order = ['commissioning_hold'] + sorted(k for k in files if k not in ('commissioning_hold','boot.py','main.py')) + ['main.py','boot.py']
for rel in order:
    remote('fs','cp', str(STAGE / rel), ':' + rel)
    print('Uploaded',rel,flush=True)
assert hashes(list(files)) == files, 'Uploaded hash mismatch'
untouched = {k:v for k,v in before.items() if k != 'boot.py'}
assert hashes(list(untouched)) == untouched, 'Unexpected original file change'
result = {'board_serial':'80:F1:B2:1E:B3:6C','port':PORT,
          'uploaded_sha256':files, 'preserved_sha256':untouched,
          'state':'commissioning_hold; no motion test; wireless pairing not retested'}
(ROOT / '2026-11-13_蓝色2_D2_上传校验.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(remote('exec', "import palm2_remote_ready as p; import palm2_main; from attack_control import AttackController; from drivers.palm_pwm import PalmPwmDriver; d=PalmPwmDriver(p.PALM); print('D2_GPIO',p.PALM['gpio'],'PWM_ACTIVE',d.is_active()); palm2_main.start()"))
print('UPLOAD VERIFIED; NO MOTION',flush=True)
