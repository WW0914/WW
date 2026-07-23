param(
    [Parameter(Mandatory = $true)]
    [string]$PartPath,

    [double]$RadiusLimit = 0.0,

    [string]$ResultPath
)

$runner = 'D:\Program Files\Siemens\NX2306\NXBIN\run_journal.exe'
$journal = 'C:\Users\10482\Desktop\ZD\tools\ZD_StraightLifterReview.py'

if (-not (Test-Path -LiteralPath $PartPath)) {
    throw "PRT 文件不存在：$PartPath"
}

if ([string]::IsNullOrWhiteSpace($ResultPath)) {
    $directory = Split-Path -Parent $PartPath
    $name = [IO.Path]::GetFileNameWithoutExtension($PartPath)
    $ResultPath = Join-Path $directory ($name + '_审查结果.json')
}

& $runner $journal -args $PartPath $ResultPath $RadiusLimit.ToString([Globalization.CultureInfo]::InvariantCulture)
if ($LASTEXITCODE -ne 0) {
    throw "NX 自动审查失败，退出码：$LASTEXITCODE"
}

Get-Content -LiteralPath $ResultPath -Raw -Encoding UTF8
