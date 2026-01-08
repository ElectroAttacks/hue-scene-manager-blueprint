#!/usr/bin/env pwsh
# Script to update version in blueprint
param(
    [Parameter(Mandatory=$true)]
    [string]$NewVersion
)

$blueprintFile = "hue-scene-refresher.yaml"

Write-Host "Updating blueprint version to $NewVersion..." -ForegroundColor Cyan

# Read the file
$content = Get-Content $blueprintFile -Raw -Encoding UTF8

# Update the version in the name field
$content = $content -replace 'name: Hue Scene Refresher \(v[\d\.]+\)', "name: Hue Scene Refresher (v$NewVersion)"

# Write back
$content | Set-Content $blueprintFile -NoNewline -Encoding UTF8

Write-Host "Blueprint updated successfully!" -ForegroundColor Green
