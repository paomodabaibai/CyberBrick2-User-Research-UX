param(
    [Parameter(Mandatory=$true)][ValidatePattern('^COM\d+$')][string]$Port,
    [switch]$ConfirmedReceiver
)
$ErrorActionPreference = 'Stop'
if (-not $ConfirmedReceiver) { throw '先确认该串口是拳头接收板，再加 -ConfirmedReceiver。' }
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw '先在仓库根目录建立 .venv 并安装 requirements-serial.txt。' }
function Run-Mp([string[]]$Arguments) {
    & $python -m mpremote @Arguments
    if ($LASTEXITCODE -ne 0) { throw 'mpremote 失败，停止后续步骤。' }
}
# Taking the REPL interrupts the current app. No test is automatically run.
Run-Mp @('connect', $Port, 'resume', 'exec', "import machine; assert machine.Pin(10,machine.Pin.IN).value()==0, 'not receiver'")
Run-Mp @('connect', $Port, 'resume', 'exec', "from bbl.motors import MotorsController; assert hasattr(MotorsController,'set_speed') and hasattr(MotorsController,'stop'), 'motor API missing'; import bbl.motors as m; assert m.MOTOR1_PIN1==4 and m.MOTOR1_PIN2==5, 'unexpected M1 pins'")
# Back up both destination files if present, before writing either.
$backup = Join-Path $root ('work\punch_backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force $backup | Out-Null
foreach ($name in @('otto_oscillator.py','second_punch_remote.py')) {
    $probe = "import os; print('$name' in os.listdir())"
    $exists = & $python -m mpremote connect $Port resume exec $probe
    if ($LASTEXITCODE -ne 0) { throw '板端文件检查失败。' }
    if (($exists -join "`n") -match 'True') {
        Run-Mp @('connect', $Port, 'resume', 'fs', 'cp', (':' + $name), (Join-Path $backup $name))
    }
}
foreach ($name in @('otto_oscillator.py','second_punch_remote.py')) {
    $source = Join-Path $PSScriptRoot $name
    Run-Mp @('connect', $Port, 'resume', 'fs', 'cp', $source, (':' + $name))
    $verify = Join-Path $backup ('verify_' + $name)
    Run-Mp @('connect', $Port, 'resume', 'fs', 'cp', (':' + $name), $verify)
    if ((Get-FileHash $source).Hash -ne (Get-FileHash $verify).Hash) { throw "上传校验失败：$name" }
}
Write-Host '两个测试文件已上传并回读校验。没有运行测试，没有修改 boot.py/main.py。'
Write-Host ('备份：' + $backup)
Write-Host '下一步进入 REPL：import second_punch_remote as p; p.monitor(15)'
