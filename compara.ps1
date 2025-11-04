# Defina os caminhos dos diretorios
$dir1 = "C:\Users\AltF4\Documents\MACTESTE_FAIL\MACTESTER\release_1.0"
$dir2 = "C:\Users\AltF4\Documents\MACTESTER\release_1.0"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "COMPARANDO DIRETORIOS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Dir1: $dir1"
Write-Host "Dir2: $dir2"
Write-Host ""

# Obtem lista de arquivos de ambos os diretorios
$files1 = Get-ChildItem -Path $dir1 -Recurse -File | Select-Object Name, Length, @{Name="RelativePath";Expression={$_.FullName.Replace($dir1, "")}}
$files2 = Get-ChildItem -Path $dir2 -Recurse -File | Select-Object Name, Length, @{Name="RelativePath";Expression={$_.FullName.Replace($dir2, "")}}

Write-Host "Total de arquivos no Dir1: $($files1.Count)" -ForegroundColor Green
Write-Host "Total de arquivos no Dir2: $($files2.Count)" -ForegroundColor Green

# Arquivos apenas no dir1
$onlyInDir1 = $files1 | Where-Object { $_.RelativePath -notin $files2.RelativePath }
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "ARQUIVOS APENAS NO DIR1 (MACTESTE_FAIL)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
if ($onlyInDir1.Count -eq 0) {
    Write-Host "Nenhum arquivo exclusivo encontrado." -ForegroundColor Green
} else {
    $onlyInDir1 | Format-Table Name, Length, RelativePath -AutoSize
}

# Arquivos apenas no dir2
$onlyInDir2 = $files2 | Where-Object { $_.RelativePath -notin $files1.RelativePath }
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "ARQUIVOS APENAS NO DIR2 (MACTESTER)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
if ($onlyInDir2.Count -eq 0) {
    Write-Host "Nenhum arquivo exclusivo encontrado." -ForegroundColor Green
} else {
    $onlyInDir2 | Format-Table Name, Length, RelativePath -AutoSize
}

# Arquivos com tamanhos diferentes
Write-Host "`n========================================" -ForegroundColor Red
Write-Host "ARQUIVOS COM TAMANHOS DIFERENTES" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
$differentSizes = @()
foreach ($file1 in $files1) {
    $file2 = $files2 | Where-Object { $_.RelativePath -eq $file1.RelativePath }
    if ($file2 -and $file1.Length -ne $file2.Length) {
        $differentSizes += [PSCustomObject]@{
            Arquivo = $file1.Name
            CaminhoRelativo = $file1.RelativePath
            TamanhoDir1 = $file1.Length
            TamanhoDir2 = $file2.Length
            Diferenca = $file1.Length - $file2.Length
        }
    }
}

if ($differentSizes.Count -eq 0) {
    Write-Host "Todos os arquivos comuns tem o mesmo tamanho." -ForegroundColor Green
} else {
    $differentSizes | Format-Table Arquivo, TamanhoDir1, TamanhoDir2, Diferenca -AutoSize
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RESUMO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Arquivos apenas no Dir1: $($onlyInDir1.Count)" -ForegroundColor Yellow
Write-Host "Arquivos apenas no Dir2: $($onlyInDir2.Count)" -ForegroundColor Yellow
Write-Host "Arquivos com tamanhos diferentes: $($differentSizes.Count)" -ForegroundColor Red
Write-Host ""