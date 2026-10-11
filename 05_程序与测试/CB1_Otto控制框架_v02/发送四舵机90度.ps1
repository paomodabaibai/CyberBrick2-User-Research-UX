param(
    [string]$Port
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$candidates = @(
    $env:MPREMOTE_EXE,
    (Join-Path $projectRoot '.venv\Scripts\mpremote.exe'),
    (Join-Path $PSScriptRoot '..\serial_runtime\Scripts\mpremote.exe')
)
$mpremote = $null
foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path -LiteralPath $candidate)) { $mpremote = $candidate; break }
}
if (-not $mpremote) {
    $command = Get-Command mpremote -ErrorAction SilentlyContinue
    if ($command) { $mpremote = $command.Source }
}
if (-not $mpremote) {
    throw '找不到 mpremote。新电脑先运行：py -m venv .venv；.\.venv\Scripts\python.exe -m pip install -r requirements-serial.txt'
}
$boardFile = Join-Path $PSScriptRoot 'hold_90_cb1.py'
if (-not (Test-Path -LiteralPath $boardFile)) { throw "找不到板端脚本：$boardFile" }

if (-not $Port) {
    $ports = @(Get-PnpDevice -Class Ports -PresentOnly |
        Where-Object { $_.InstanceId -match 'VID_303A&PID_1001' -and $_.FriendlyName -match '\(COM\d+\)' } |
        ForEach-Object { [regex]::Match($_.FriendlyName, 'COM\d+').Value })
    if ($ports.Count -ne 1) {
        throw "检测到 $($ports.Count) 块候选接收板。请查看设备管理器后指定 -Port COMx；候选：$($ports -join ', ')"
    }
    $Port = $ports[0]
}
if ($Port -notmatch '^COM\d+$') { throw '端口格式应为 COM7、COM9 等' }

Write-Host "检查 $Port 是否为 CB1 接收板（GPIO10=0）..."
& $mpremote connect $Port resume exec "import machine; assert machine.Pin(10,machine.Pin.IN).value() == 0, 'not a CB1 receiver'"
if ($LASTEXITCODE -ne 0) { throw '接收板身份检查失败；未上传脚本' }

Write-Host "上传四舵机中位脚本至 $Port ..."
& $mpremote connect $Port resume fs cp $boardFile :hold_90_cb1.py
if ($LASTEXITCODE -ne 0) { throw '上传失败' }

Write-Host '发送 90°命令并持续保持；此时可安装舵盘。'
& $mpremote connect $Port resume exec 'import hold_90_cb1 as h; h.hold()'
if ($LASTEXITCODE -ne 0) { throw '中位命令失败；请检查板端日志及供电' }
Write-Host '完成。断电/重启会解除保持；要主动释放可在 REPL 调 h.off()。'
