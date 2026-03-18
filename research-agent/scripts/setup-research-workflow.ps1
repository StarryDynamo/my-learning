# Add Daily Research Digest workflow to the repo root (for my-learning or any repo that has research-agent as a subfolder).
#
# Option A - Run from your my-learning repo root (after pulling latest research-agent with the workflow file):
#   cd C:\path\to\my-learning
#   .\research-agent\scripts\setup-research-workflow.ps1
#
# Option B - Run from agents folder: copy workflow from agents into your my-learning repo:
#   cd C:\Users\heave\agents
#   .\research-agent\scripts\setup-research-workflow.ps1 -RepoRoot "C:\path\to\my-learning"
#   (Uses the workflow file from agents; my-learning does not need to have it yet.)

param(
    [string] $RepoRoot = ""
)

$ErrorActionPreference = "Stop"

if ($RepoRoot) {
    $root = (Resolve-Path $RepoRoot).Path
    # When RepoRoot is given, use workflow from this script's repo (agents)
    $scriptDir = (Get-Item $PSScriptRoot).Parent  # research-agent folder
    $ghDir = Join-Path $scriptDir ".github"
    $wfDir = Join-Path $ghDir "workflows"
    $sourceFile = Join-Path $wfDir "daily-research-digest-at-repo-root.yml"
    $sourceFile = (Resolve-Path $sourceFile).Path
} else {
    # Assume script is at repo/research-agent/scripts/setup-research-workflow.ps1
    $researchAgentDir = (Get-Item $PSScriptRoot).Parent
    $root = (Get-Item $researchAgentDir).Parent.FullName
    $raDir = Join-Path $root "research-agent"
    $ghDir = Join-Path $raDir ".github"
    $wfDir = Join-Path $ghDir "workflows"
    $sourceFile = Join-Path $wfDir "daily-research-digest-at-repo-root.yml"
}

$workflowDir = Join-Path (Join-Path $root ".github") "workflows"
$targetFile = Join-Path $workflowDir "daily-research-digest.yml"

if (-not (Test-Path (Join-Path $root "research-agent"))) {
    Write-Error "Repo root should contain research-agent/. Current root: $root"
    exit 1
}

if (-not (Test-Path $sourceFile)) {
    Write-Error "Source workflow not found: $sourceFile"
    exit 1
}

if (-not (Test-Path $workflowDir)) {
    New-Item -ItemType Directory -Path $workflowDir -Force | Out-Null
    Write-Host "Created $workflowDir"
}

Copy-Item -Path $sourceFile -Destination $targetFile -Force
Write-Host "Added: $targetFile"
Write-Host ""
Write-Host "Next: commit and push, and ensure ANTHROPIC_API_KEY is set in repo Secrets (Settings -> Secrets and variables -> Actions)."
