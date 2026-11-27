# =============================================================================
# test-quality.ps1 - Chequeo Automático de Calidad, Sintaxis y Seguridad (0 Tokens)
# Gauntlet Gate Automático: Ejecuta validaciones estáticas locales sin costo de IA.
# =============================================================================

param (
    [string]$TargetDir = $PSScriptRoot
)

$errorsFound = 0
$warningsFound = 0

function Write-TestResult {
    param([string]$Name, [bool]$Pass, [string]$Details = "")
    if ($Pass) {
        Write-Host "  [PASS] $Name" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $Name - $Details" -ForegroundColor Red
        $script:errorsFound++
    }
}

function Write-TestWarn {
    param([string]$Name, [string]$Details)
    Write-Host "  [WARN] $Name - $Details" -ForegroundColor Yellow
    $script:warningsFound++
}

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "   GAUNTLET AUTOMATIC CHECK (Zero-Token Local Validator)  " -ForegroundColor Cyan
Write-Host "   Directorio: $TargetDir" -ForegroundColor DarkCyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Recorrido único de archivos (optimizado para SMB y disco local)
$allFiles = Get-ChildItem -Path $TargetDir -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\(\.git|vendor|node_modules|__pycache__)\\' }

# 1. Validación de Sintaxis PowerShell (.ps1)
Write-Host "[1/6] Validando sintaxis de scripts PowerShell (.ps1)..." -ForegroundColor White
$psScripts = $allFiles | Where-Object { $_.Extension -eq ".ps1" }

foreach ($script in $psScripts) {
    $content = Get-Content -Path $script.FullName -Raw -Encoding utf8
    $tokens = $null
    $errors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseInput($content, [ref]$tokens, [ref]$errors)
    
    $relPath = $script.FullName.Replace($TargetDir, "").TrimStart("\")
    if ($errors.Count -eq 0) {
        Write-TestResult "PS Syntax: $relPath" $true
    } else {
        $firstErr = $errors[0].Message
        Write-TestResult "PS Syntax: $relPath" $false "Línea $($errors[0].Extent.StartLineNumber): $firstErr"
    }
}

# 2. Validación de Archivos JSON (.json)
Write-Host ""
Write-Host "[2/6] Validando formato de archivos JSON (.json)..." -ForegroundColor White
$jsonFiles = $allFiles | Where-Object { $_.Extension -eq ".json" }

foreach ($jsonFile in $jsonFiles) {
    $relPath = $jsonFile.FullName.Replace($TargetDir, "").TrimStart("\")
    try {
        $content = Get-Content -Path $jsonFile.FullName -Raw -Encoding utf8
        $null = ConvertFrom-Json -InputObject $content -ErrorAction Stop
        Write-TestResult "JSON Parse: $relPath" $true
    } catch {
        Write-TestResult "JSON Parse: $relPath" $false $_.Exception.Message
    }
}

# 3. Auditoría de Seguridad (Búsqueda de Secretos en texto plano en código y Markdown)
Write-Host ""
Write-Host "[3/6] Auditando presencia de secretos y credenciales..." -ForegroundColor White
$sensitivePatterns = @(
    '(?i)password\s*=\s*["''][^"'']{4,}["'']',
    '(?i)api[_-]?key\s*=\s*["''][^"'']{8,}["'']',
    '(?i)secret\s*=\s*["''][^"'']{8,}["'']',
    '(?i)token\s*=\s*["''][^"'']{8,}["'']',
    '(?i)(contrase[ñn]a|password)\s*(permanente\s*)?[:=]?\s*[`"''''](?![<\$])[^`"'''']{4,}[`"'''']',
    'BEGIN (RSA|EC|OPENSSH) PRIVATE KEY'
)

$textExts = @(".ps1", ".json", ".yml", ".yaml", ".md", ".js", ".py")
$textFiles = $allFiles | Where-Object { $textExts -contains $_.Extension -and $_.Name -ne "test-quality.ps1" }

$secretViolations = 0
foreach ($file in $textFiles) {
    $content = Get-Content -Path $file.FullName -Raw -Encoding utf8
    if ([string]::IsNullOrEmpty($content)) { continue }
    $relPath = $file.FullName.Replace($TargetDir, "").TrimStart("\")
    
    foreach ($pattern in $sensitivePatterns) {
        if ($content -match $pattern) {
            Write-TestResult "Security Secret Leak: $relPath" $false "Posible secreto detectado por regex: $pattern"
            $secretViolations++
            break
        }
    }
}
if ($secretViolations -eq 0) {
    Write-TestResult "Seguridad: Cero secretos en texto plano" $true
}

# 4. Verificación de Límites de Contexto (Tokens Saver: AGENTS.md, agy_config.md, snapshot <= 8 líneas)
Write-Host ""
Write-Host "[4/6] Verificando límites de contexto (Economía de Tokens)..." -ForegroundColor White

$agentsPath = Join-Path $TargetDir "AGENTS.md"
if (Test-Path $agentsPath) {
    $size = (Get-Item $agentsPath).Length
    if ($size -le 1536) {
        Write-TestResult "AGENTS.md presente y compacto ($size bytes <= 1.5 KB)" $true
    } elseif ($size -le 2048) {
        Write-TestWarn "AGENTS.md supera 1.5 KB ideal ($size bytes)" "Mantener < 1.5 KB según agent-constructor"
    } else {
        Write-TestWarn "AGENTS.md excede tamaño recomendado" "Tamaño: $size bytes (Recomendado < 1.5 KB)"
    }
} else {
    Write-TestWarn "AGENTS.md ausente" "Se recomienda crear AGENTS.md en la raíz del proyecto"
}

$agyConfigPath = Join-Path $TargetDir "agy_config.md"
if (Test-Path $agyConfigPath) {
    $size = (Get-Item $agyConfigPath).Length
    $rawAgy = Get-Content $agyConfigPath -Raw -Encoding utf8
    $hasSnapshot = $rawAgy -match '## Estado Actual \(snapshot\)'
    
    # Verificar longitud del bloque snapshot (máx 8 líneas según project-snapshot)
    $snapshotLines = 0
    if ($hasSnapshot -and $rawAgy -match '(?ms)^## Estado Actual \(snapshot\)\r?\n(.*?)(?=\r?\n## |\z)') {
        $blockText = $Matches[0].TrimEnd()
        $snapshotLines = ($blockText -split '\r?\n').Count
    }

    if (-not $hasSnapshot) {
        Write-TestResult "agy_config.md tiene bloque snapshot" $false "Falta el bloque '## Estado Actual (snapshot)'"
    } elseif ($snapshotLines -gt 8) {
        Write-TestWarn "Bloque snapshot en agy_config.md supera 8 líneas ($snapshotLines líneas)" "Reducir según project-snapshot"
    } elseif ($size -le 3072) {
        Write-TestResult "agy_config.md compacto ($size bytes <= 3 KB) y snapshot ($snapshotLines líneas <= 8)" $true
    } else {
        Write-TestWarn "agy_config.md excede 3 KB" "Tamaño: $size bytes (Aplica context-splitter)"
    }
}

# 5. Compatibilidad ARM64 en Docker (NAS)
Write-Host ""
Write-Host "[5/6] Verificando compatibilidad de contenedores Docker (NAS ARM64)..." -ForegroundColor White
$dockerFiles = $allFiles | Where-Object { $_.Name -like "*docker-compose*.yml" }

foreach ($dFile in $dockerFiles) {
    $relPath = $dFile.FullName.Replace($TargetDir, "").TrimStart("\")
    $content = Get-Content -Path $dFile.FullName -Raw -Encoding utf8
    
    if ($content -match 'platform:\s*linux/amd64') {
        Write-TestWarn "Docker ARM64: $relPath" "Emulación forzada linux/amd64 detectada. Afectará el rendimiento del NAS."
    } else {
        Write-TestResult "Docker Arch: $relPath" $true
    }
}

# 6. Plantillas AutoText: variables definidas/usadas y politica de datos personales
Write-Host ""
Write-Host "[6/6] Validando plantillas AutoText (variables y politica de datos personales)..." -ForegroundColor White
$webDir = Join-Path $TargetDir "web"
$policyPath = Join-Path $webDir "politica_datos_personales.json"
$policy = $null
if (Test-Path $policyPath) {
    $policy = Get-Content -Path $policyPath -Raw -Encoding utf8 | ConvertFrom-Json
} else {
    Write-TestWarn "Politica de datos personales ausente" "No existe web\politica_datos_personales.json; se omite la verificacion de politica"
}

$tplFiles = @()
if (Test-Path $webDir) {
    $tplFiles = Get-ChildItem -Path $webDir -Filter *.html -File | Where-Object { $_.Name -notin @("Autotext_Final.html", "index.html") }
}
$tplChecked = 0
foreach ($tpl in $tplFiles) {
    $raw = Get-Content -Path $tpl.FullName -Raw -Encoding utf8
    $mVars = [regex]::Match($raw, '(?s)<script id="variables-data" type="application/json">(.*?)</script>')
    $mText = [regex]::Match($raw, '(?s)<script id="template-text-data" type="text/plain">(.*?)</script>')
    if (-not $mVars.Success -or -not $mText.Success) { continue }
    $tplChecked++
    $stem = [IO.Path]::GetFileNameWithoutExtension($tpl.Name)
    $text = [System.Net.WebUtility]::HtmlDecode($mText.Groups[1].Value)
    try {
        $vars = @($mVars.Groups[1].Value | ConvertFrom-Json -ErrorAction Stop)
    } catch {
        Write-TestResult "Plantilla ${stem}: JSON de variables" $false $_.Exception.Message
        continue
    }
    $ids = @($vars | ForEach-Object { $_.id })

    # 6a. Variables duplicadas, usadas-sin-definir y definidas-sin-usar
    $dups = @($ids | Group-Object | Where-Object { $_.Count -gt 1 } | ForEach-Object { $_.Name })
    $used = @([regex]::Matches($text, '\{\{([A-Za-z0-9_]+)\}\}') | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique)
    $undefined = @($used | Where-Object { $ids -notcontains $_ })
    $unused = @($ids | Where-Object { $used -notcontains $_ })
    if ($dups.Count -gt 0) { Write-TestResult "Plantilla ${stem}: ids unicos" $false ("Duplicadas: " + ($dups -join ", ")) }
    if ($undefined.Count -gt 0) { Write-TestResult "Plantilla ${stem}: variables definidas" $false ("Usadas sin definir: " + ($undefined -join ", ")) }
    if ($unused.Count -gt 0) { Write-TestWarn "Plantilla ${stem}" ("Variables definidas pero no usadas: " + ($unused -join ", ")) }

    # 6b. Politica de datos personales (nombre / ID / fecha)
    if ($null -ne $policy) {
        $s = ($stem -replace '[^A-Za-z0-9]', '').ToUpper()
        $denied = $false; $allowed = $false
        foreach ($k in @($policy.deny_stems)) { if ($s -like "*$k*") { $denied = $true } }
        if (-not $denied) {
            foreach ($k in @($policy.allow_stems)) { if ($s -like "*$k*") { $allowed = $true } }
            if (-not $allowed -and $policy.allow_content_regex -and ($text -match "(?i)$($policy.allow_content_regex)")) { $allowed = $true }
        }
        if (-not $allowed) {
            $personal = @($vars | Where-Object { "$($_.id) $($_.label)" -match "(?i)$($policy.personal_label_regex)" } | ForEach-Object { $_.id })
            if ($personal.Count -gt 0) {
                $msg = "Variables personales en plantilla sin receta/recomendaciones: " + ($personal -join ", ")
                if ($denied) { Write-TestResult "Politica datos personales: $stem" $false $msg }
                else { Write-TestWarn "Politica datos personales: $stem" $msg }
            }
        }
    }
}
if ($tplChecked -gt 0 -and $errorsFound -eq 0) {
    Write-TestResult "Plantillas AutoText validadas ($tplChecked)" $true
}

# Resumen Final
Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
if ($errorsFound -eq 0) {
    Write-Host "  RESULTADO: GAUNTLET SUPERADO [0 Errores | $warningsFound Advertencias]" -ForegroundColor Green
    Write-Host "===========================================================" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "  RESULTADO: GAUNTLET FALLIDO [$errorsFound Errores | $warningsFound Advertencias]" -ForegroundColor Red
    Write-Host "  Corrige los fallos antes de reportar la tarea o hacer commit." -ForegroundColor Red
    Write-Host "===========================================================" -ForegroundColor Cyan
    exit 1
}
