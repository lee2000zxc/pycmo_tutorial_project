param(
    [Parameter(Mandatory = $true)]
    [string]$ScenarioWindowTitle,
    [double]$TimeoutSeconds = 60,
    [double]$MenuDelaySeconds = 1,
    [ValidateSet(1, 2, 5)]
    [int]$TargetTimeCompression = 5
)

$ErrorActionPreference = "Stop"

$shell = New-Object -ComObject WScript.Shell

if (-not $shell.AppActivate($ScenarioWindowTitle)) {
    throw "CMO scenario window not found: $ScenarioWindowTitle"
}

Start-Sleep -Milliseconds ([int]($MenuDelaySeconds * 1000))

# File -> Load Recent -> first item.
# Opening the submenu with Right automatically selects its first item.
# Do not send Home here: CMO can move the focus back to the parent menu.
$shell.SendKeys("%f")
Start-Sleep -Milliseconds 300
$shell.SendKeys("{DOWN 6}")
Start-Sleep -Milliseconds 300
$shell.SendKeys("{RIGHT}")
Start-Sleep -Milliseconds ([int]($MenuDelaySeconds * 1000))
$shell.SendKeys("{ENTER}")

# Load the recent scenario directly without side-selection automation.
# Then activate the map window, set the requested compression, and start.
Start-Sleep -Milliseconds 2000
if (-not $shell.AppActivate($ScenarioWindowTitle)) {
    throw "CMO scenario window not found after load: $ScenarioWindowTitle"
}
Start-Sleep -Milliseconds 500

# Enter resets compression to 1x. Each Plus advances 1x -> 2x -> 5x.
$shell.SendKeys("{ENTER}")
Start-Sleep -Milliseconds 300

if ($TargetTimeCompression -ge 2) {
    $shell.SendKeys("%g")
    Start-Sleep -Milliseconds 300
    $shell.SendKeys("{DOWN 1}")
    Start-Sleep -Milliseconds 300
    $shell.SendKeys("{ENTER}")
    Start-Sleep -Milliseconds 300
}
if ($TargetTimeCompression -ge 5) {
    $shell.SendKeys("%g")
    Start-Sleep -Milliseconds 300
    $shell.SendKeys("{DOWN 1}")
    Start-Sleep -Milliseconds 300
    $shell.SendKeys("{ENTER}")
    Start-Sleep -Milliseconds 300
}
Start-Sleep -Milliseconds 300
$shell.SendKeys("{ }")
Start-Sleep -Milliseconds 300
Write-Output (
    "Simulation started at " +
    $TargetTimeCompression +
    "x time compression."
)
exit 0
