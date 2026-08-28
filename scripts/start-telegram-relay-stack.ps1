[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $TelegramMcpRoot,

    [Parameter(Mandatory = $true)]
    [string] $TunnelClientPath,

    [string] $TunnelProfile = "telegram",
    [string] $PythonPath,
    [string] $RuntimeDirectory = (Join-Path $env:TEMP "chatgpt-telegram-relay"),
    [int] $McpPort = 8765,
    [int] $TunnelHealthPort = 8080,
    [ValidateRange(5, 120)]
    [int] $StartupTimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-TcpEndpoint {
    param([int] $Port)

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $task = $client.ConnectAsync("127.0.0.1", $Port)
        if (-not $task.Wait(750)) {
            return $false
        }
        return $client.Connected
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Test-TunnelReady {
    param([int] $Port)

    try {
        $response = Invoke-WebRequest `
            -UseBasicParsing `
            -Uri "http://127.0.0.1:$Port/readyz" `
            -TimeoutSec 2
        return $response.StatusCode -eq 200 -and $response.Content.Trim() -eq "ready"
    }
    catch {
        return $false
    }
}

function Wait-Until {
    param(
        [scriptblock] $Condition,
        [string] $FailureMessage
    )

    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    while ($timer.Elapsed.TotalSeconds -lt $StartupTimeoutSeconds) {
        if (& $Condition) {
            return
        }
        Start-Sleep -Milliseconds 300
    }
    throw $FailureMessage
}

$mcpRoot = (Resolve-Path -LiteralPath $TelegramMcpRoot).Path
$tunnelExe = (Resolve-Path -LiteralPath $TunnelClientPath).Path

if (-not $PythonPath) {
    $PythonPath = Join-Path $mcpRoot ".venv\Scripts\python.exe"
}
$pythonExe = (Resolve-Path -LiteralPath $PythonPath).Path

if (-not (Test-Path -LiteralPath (Join-Path $mcpRoot "main.py") -PathType Leaf)) {
    throw "telegram-mcp main.py was not found under the supplied root."
}
if ([System.IO.Path]::GetExtension($tunnelExe) -ne ".exe") {
    throw "TunnelClientPath must resolve to a Windows executable."
}

New-Item -ItemType Directory -Force -Path $RuntimeDirectory | Out-Null
$runtimeRoot = (Resolve-Path -LiteralPath $RuntimeDirectory).Path
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"

$result = [ordered]@{
    mcp = [ordered]@{ status = "existing"; pid = $null; stdout = $null; stderr = $null }
    tunnel = [ordered]@{ status = "existing"; pid = $null; stdout = $null; stderr = $null }
}

if (-not (Test-TcpEndpoint -Port $McpPort)) {
    $mcpStdout = Join-Path $runtimeRoot "telegram-mcp-$stamp.stdout.log"
    $mcpStderr = Join-Path $runtimeRoot "telegram-mcp-$stamp.stderr.log"
    $process = Start-Process `
        -FilePath $pythonExe `
        -ArgumentList @("main.py") `
        -WorkingDirectory $mcpRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $mcpStdout `
        -RedirectStandardError $mcpStderr `
        -PassThru
    $result.mcp = [ordered]@{
        status = "started"
        pid = $process.Id
        stdout = $mcpStdout
        stderr = $mcpStderr
    }
    Wait-Until -Condition { Test-TcpEndpoint -Port $McpPort } `
        -FailureMessage "telegram-mcp did not listen on port $McpPort within the timeout."
}

if (-not (Test-TunnelReady -Port $TunnelHealthPort)) {
    if (Test-TcpEndpoint -Port $TunnelHealthPort) {
        throw "Tunnel health port $TunnelHealthPort is occupied but /readyz is not ready."
    }

    $tunnelStdout = Join-Path $runtimeRoot "tunnel-client-$stamp.stdout.log"
    $tunnelStderr = Join-Path $runtimeRoot "tunnel-client-$stamp.stderr.log"
    $process = Start-Process `
        -FilePath $tunnelExe `
        -ArgumentList @("run", "--profile", $TunnelProfile) `
        -WorkingDirectory $runtimeRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $tunnelStdout `
        -RedirectStandardError $tunnelStderr `
        -PassThru
    $result.tunnel = [ordered]@{
        status = "started"
        pid = $process.Id
        stdout = $tunnelStdout
        stderr = $tunnelStderr
    }
    Wait-Until -Condition { Test-TunnelReady -Port $TunnelHealthPort } `
        -FailureMessage "tunnel-client did not become ready on port $TunnelHealthPort within the timeout."
}

$result.mcp["reachable"] = Test-TcpEndpoint -Port $McpPort
$result.tunnel["ready"] = Test-TunnelReady -Port $TunnelHealthPort
$result | ConvertTo-Json -Depth 5
