param(
    [string]$HostName = '192.168.1.107',
    [string]$RemoteUser = 'windows11',
    [ValidatePattern('^COM\d+$')][string]$Port,
    [string]$FilePath,
    [switch]$Run
)

$ErrorActionPreference = 'Stop'
$target = "${RemoteUser}@${HostName}"
$sshOptions = @('-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5')

function Invoke-RemotePowerShell([string]$Script) {
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Script))
    & ssh @sshOptions $target "powershell -NoProfile -NonInteractive -EncodedCommand $encoded"
    if ($LASTEXITCODE -ne 0) { throw "远程命令失败：$target" }
}

# Read-only probe. Board identity must be confirmed before selecting a COM port.
Invoke-RemotePowerShell 'Get-PnpDevice -Class Ports -PresentOnly | Where-Object { $_.InstanceId -match "VID_303A&PID_1001" } | Select-Object FriendlyName,InstanceId | Format-List'

if (-not $FilePath) {
    Write-Host '只读检查完成。上传时需指定 -Port COMx -FilePath 本地脚本.py。'
    exit 0
}
if (-not $Port) { throw '上传前必须指定已确认的接收板串口，例如 -Port COM6。' }
$localFile = (Resolve-Path -LiteralPath $FilePath).Path
if ([IO.Path]::GetExtension($localFile) -ne '.py') { throw '目前仅支持上传 MicroPython .py 文件。' }
$boardName = [IO.Path]::GetFileName($localFile)
if ($boardName -notmatch '^[A-Za-z0-9_.-]+$') { throw '文件名请使用英文字母、数字、下划线或连字符。' }

$remoteName = 'cb1-remote-upload.py'
& scp @sshOptions $localFile "${target}:$remoteName"
if ($LASTEXITCODE -ne 0) { throw '复制到远程电脑失败；接收板未更改。' }

$runLine = ''
if ($Run) {
    if ($boardName -eq 'main.py' -or $boardName -eq 'boot.py') {
        throw 'main.py/boot.py 不允许通过 -Run 立即执行；请先单独核对启动行为。'
    }
    $module = [IO.Path]::GetFileNameWithoutExtension($boardName)
    $runLine = '& $mp connect $port resume exec "import ' + $module + '"; if ($LASTEXITCODE -ne 0) { throw "板上运行失败" }'
}
$remoteScript = @"
`$ErrorActionPreference = 'Stop'
`$port = '$Port'
`$source = Join-Path `$env:USERPROFILE '$remoteName'
`$boardName = '$boardName'
`$mp = (Get-Command mpremote -ErrorAction SilentlyContinue).Source
if (-not `$mp) { throw '远程电脑未安装 mpremote；先运行 py -m pip install mpremote' }
& `$mp connect `$port resume exec "import machine; assert machine.Pin(10,machine.Pin.IN).value() == 0, 'not CB1 receiver'"
if (`$LASTEXITCODE -ne 0) { throw '接收板身份检查失败，未上传' }
& `$mp connect `$port resume fs cp `$source (':' + `$boardName)
if (`$LASTEXITCODE -ne 0) { throw '上传失败' }
$runLine
Write-Host ('已上传到 ' + `$port + ':' + `$boardName)
"@
Invoke-RemotePowerShell $remoteScript
