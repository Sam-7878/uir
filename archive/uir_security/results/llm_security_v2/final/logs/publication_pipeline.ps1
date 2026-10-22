param(
    [int]$WaitForPid = 0
)

$ErrorActionPreference = 'Stop'
$RepoLinux = '/mnt/d/_Work/goat_bank/uir'
$LogDir = 'D:\_Work\goat_bank\uir\results\llm_security_v2\final\logs'
$StatePath = Join-Path $LogDir 'publication_pipeline.state.json'

function Write-State {
    param(
        [string]$Step,
        [string]$Status,
        [int]$ExitCode = 0
    )

    $state = [ordered]@{
        updated_at = (Get-Date).ToUniversalTime().ToString('o')
        step = $Step
        status = $Status
        exit_code = $ExitCode
    }
    $state | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding utf8
}

function Invoke-UirStep {
    param(
        [string]$Name,
        [string]$Command
    )

    Write-State -Step $Name -Status 'RUNNING'
    $stdout = Join-Path $LogDir ($Name + '.stdout.log')
    $stderr = Join-Path $LogDir ($Name + '.stderr.log')
    $linux = "cd $RepoLinux && source ../.venv/bin/activate && export PYTHONUNBUFFERED=1 && $Command"
    $argLine = '-d Ubuntu -- bash -lc "' + $linux + '"'
    $process = Start-Process -FilePath 'wsl.exe' -ArgumentList $argLine -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if ($process.ExitCode -ne 0) {
        Write-State -Step $Name -Status 'FAILED' -ExitCode $process.ExitCode
        throw "Publication pipeline step '$Name' failed with exit code $($process.ExitCode)."
    }
    Write-State -Step $Name -Status 'COMPLETED'
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if ($WaitForPid -gt 0) {
    Write-State -Step 'wait-for-active-development' -Status 'RUNNING'
    Wait-Process -Id $WaitForPid -ErrorAction SilentlyContinue
}

$results = 'results/llm_security_v2/final'
$dev = 'evaluation/llm_security/datasets/security_benchmark_v2_development.jsonl'
$heldout = 'evaluation/llm_security/datasets/security_benchmark_v2_heldout.jsonl'
$common = "--backend phi35-transformers --results $results --runs 3 --batch-size 16 --resume"

Invoke-UirStep -Name '01-development-baselines' -Command "python -m evaluation.llm_security.run_security_benchmark_v2 $common --dataset $dev --split development"
Invoke-UirStep -Name '02-heldout-baselines' -Command "python -m evaluation.llm_security.run_security_benchmark_v2 $common --dataset $heldout --split heldout"
Invoke-UirStep -Name '03-development-ablation' -Command "python -m evaluation.llm_security.run_ablation_study_v2 $common --dataset $dev --split development"
Invoke-UirStep -Name '04-heldout-ablation' -Command "python -m evaluation.llm_security.run_ablation_study_v2 $common --dataset $heldout --split heldout"
Invoke-UirStep -Name '05-development-multi-knockout' -Command "python -m evaluation.llm_security.run_multi_knockout $common --dataset $dev --split development"
Invoke-UirStep -Name '06-heldout-multi-knockout' -Command "python -m evaluation.llm_security.run_multi_knockout $common --dataset $heldout --split heldout"
Invoke-UirStep -Name '07-publication-report' -Command "python -m evaluation.llm_security.generate_publication_report --results $results --repo-root ."
Invoke-UirStep -Name '08-strict-validation' -Command "python -m evaluation.llm_security.validate_results --results $results --require-publication-eligible"

Write-State -Step 'publication-pipeline' -Status 'COMPLETED'
