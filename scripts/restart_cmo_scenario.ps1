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
$restartedFromEvaluation = $false

# A completed scenario opens Player Evaluation after Scenario End is closed.
# Its third Tab stop is "Restart From Save" in the current CMO UI.  Use that
# button when available so the normal File -> Load Recent path is not executed
# a second time for the same episode.
if ($shell.AppActivate("Player Evaluation")) {
    Start-Sleep -Milliseconds 300
    $shell.SendKeys("{TAB}")
    Start-Sleep -Milliseconds 300
    $shell.SendKeys("{TAB}")
    Start-Sleep -Milliseconds 300
    $shell.SendKeys("{TAB}")        
    Start-Sleep -Milliseconds 200
    $shell.SendKeys("{ENTER}")
    $restartedFromEvaluation = $true
    Start-Sleep -Milliseconds 2000
}

if (-not $restartedFromEvaluation) {
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
}

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
