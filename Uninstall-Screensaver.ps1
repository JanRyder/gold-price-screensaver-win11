param(
  [switch]$Disable
)

$desktopKey = "HKCU:\Control Panel\Desktop"

if (Test-Path $desktopKey) {
  Remove-ItemProperty -Path $desktopKey -Name "SCRNSAVE.EXE" -ErrorAction SilentlyContinue
  if ($Disable) {
    Set-ItemProperty -Path $desktopKey -Name "ScreenSaveActive" -Type String -Value "0"
  }
}

Write-Host "已移除自定义屏幕保护程序设置。"
