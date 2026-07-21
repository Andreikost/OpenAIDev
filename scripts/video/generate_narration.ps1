param(
    [Parameter(Mandatory=$true)][string]$SpecPath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$spec = Get-Content -Raw -LiteralPath $SpecPath | ConvertFrom-Json
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.SelectVoice('Microsoft Zira Desktop')
$speaker.Rate = 0
$speaker.Volume = 100

for ($index = 0; $index -lt $spec.shot_plan.Count; $index++) {
    $target = Join-Path $OutputDirectory ('scene-{0:D2}.wav' -f ($index + 1))
    $speaker.SetOutputToWaveFile($target)
    $speaker.Speak([string]$spec.shot_plan[$index].voiceover)
    $speaker.SetOutputToNull()
    Write-Output $target
}

$speaker.Dispose()
