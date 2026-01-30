param(
  [string]$ScreenSaverPath = "",
  [switch]$Enable,
  [int]$TimeoutSeconds = 300,
  [switch]$NoLockOnResume
)

$desktopKey = "HKCU:\Control Panel\Desktop"

if ([string]::IsNullOrWhiteSpace($ScreenSaverPath)) {
  $ScreenSaverPath = Join-Path -Path $PSScriptRoot -ChildPath "GoldPriceSaver.scr"
}

if (-not (Test-Path -LiteralPath $ScreenSaverPath)) {
  Write-Host "找不到屏保文件: $ScreenSaverPath"
  Write-Host "请将 -ScreenSaverPath 指向你的 .scr 文件路径。"
  exit 1
}

Set-ItemProperty -Path $desktopKey -Name "SCRNSAVE.EXE" -Type String -Value $ScreenSaverPath

if ($Enable) {
  Set-ItemProperty -Path $desktopKey -Name "ScreenSaveActive" -Type String -Value "1"
  if ($TimeoutSeconds -gt 0) {
    Set-ItemProperty -Path $desktopKey -Name "ScreenSaveTimeOut" -Type String -Value ([string]$TimeoutSeconds)
  }
}

if ($NoLockOnResume) {
  Set-ItemProperty -Path $desktopKey -Name "ScreenSaverIsSecure" -Type String -Value "0"
}

Write-Host "已设置屏幕保护程序为: $ScreenSaverPath"
Write-Host "提示：可以打开“屏幕保护程序设置”检查是否生效。"
