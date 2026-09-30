<#
.SYNOPSIS
    Tự động quét, kiểm tra sức khỏe kho sách và tìm file PDF chưa convert trong thư mục hiện tại.
.DESCRIPTION
    Chỉ cần thả file này vào bất kỳ thư mục nào và chạy, nó sẽ tự động lấy thư mục đó làm mục tiêu quét.
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Ebook Health Check & Audit Tool"

$CurrentFolder = $PSScriptRoot
if (-not $CurrentFolder) {
    $CurrentFolder = (Get-Location).Path
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       HỆ THỐNG KIỂM TRA SỨC KHỎE & QUÉT KHO SÁCH (EPUB/PDF)     " -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " [i] Thư mục đang quét: $CurrentFolder" -ForegroundColor Green
Write-Host " [i] Đang khởi chạy động cơ quét không tốn token LLM...`n" -ForegroundColor Gray

# 1. Tìm đường dẫn script audit_library.py
$ScriptPath = ""
$Candidates = @(
    "F:\Book\.agents\skills\ebook-library-audit\scripts\audit_library.py",
    "D:\github\epub1t\scripts\audit_library.py",
    "$CurrentFolder\.agents\skills\ebook-library-audit\scripts\audit_library.py",
    "$CurrentFolder\scripts\audit_library.py"
)

foreach ($c in $Candidates) {
    if (Test-Path $c) {
        $ScriptPath = $c
        break
    }
}

if (-not $ScriptPath) {
    Write-Host "[!] Không tìm thấy audit_library.py!" -ForegroundColor Red
    Write-Host "Vui lòng đảm bảo F:\Book hoặc D:\github\epub1t tồn tại." -ForegroundColor Yellow
    Pause
    exit 1
}

$ReportMd = Join-Path $CurrentFolder "health_report.md"
$ReportJson = Join-Path $CurrentFolder "health_report.json"

# 2. Thực thi lệnh quét
python $ScriptPath --path "$CurrentFolder" --report "$ReportMd" --json "$ReportJson"

if (-not (Test-Path $ReportJson)) {
    Write-Host "`n[!] Quét thất bại hoặc không tạo được báo cáo." -ForegroundColor Red
    Pause
    exit 1
}

# 3. Đọc dữ liệu JSON tóm tắt
$JsonRaw = Get-Content $ReportJson -Raw -Encoding UTF8
$JsonContent = ConvertFrom-Json $JsonRaw
$Score = $JsonContent.health_score
$Grade = $JsonContent.grade
$Summary = $JsonContent.summary

Write-Host "`n-----------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "                   TỔNG KẾT KẾT QUẢ QUÉT                         " -ForegroundColor Yellow
Write-Host "-----------------------------------------------------------------" -ForegroundColor DarkGray

if ($Score -ge 80) {
    Write-Host " Điểm sức khỏe: $Score / 100 ($Grade)" -ForegroundColor Green
} elseif ($Score -ge 65) {
    Write-Host " Điểm sức khỏe: $Score / 100 ($Grade)" -ForegroundColor Yellow
} else {
    Write-Host " Điểm sức khỏe: $Score / 100 ($Grade)" -ForegroundColor Red
}

Write-Host " - Tổng sách EPUB:              $($Summary.total_epubs)" -ForegroundColor White
Write-Host " - Tổng sách PDF:               $($Summary.total_pdfs)" -ForegroundColor White
Write-Host " - PDF chưa convert sang EPUB:  $($Summary.unconverted_pdfs)" -ForegroundColor Cyan
Write-Host " - EPUB bị hỏng (Corrupt):      $($Summary.broken_epubs)" -ForegroundColor $(if($Summary.broken_epubs -gt 0){"Red"}else{"Green"})
Write-Host " - EPUB bị âm bản (Inverted):   $($Summary.inverted_epubs)" -ForegroundColor $(if($Summary.inverted_epubs -gt 0){"Red"}else{"Green"})
Write-Host " - EPUB phình to (>15MB):       $($Summary.bloated_epubs_over_15mb)" -ForegroundColor $(if($Summary.bloated_epubs_over_15mb -gt 0){"Yellow"}else{"Green"})
Write-Host " - File rác macOS (._*):        $($Summary.mac_junk_files)" -ForegroundColor $(if($Summary.mac_junk_files -gt 0){"Yellow"}else{"Green"})
Write-Host "-----------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " Báo cáo chi tiết đã lưu tại: $ReportMd" -ForegroundColor Gray

# 4. Menu tương tác
while ($true) {
    Write-Host "`n[LỰA CHỌN THAO TÁC TIẾP THEO]:" -ForegroundColor Cyan
    Write-Host " [1] Tự động convert tất cả PDF scan chưa convert sang EPUB 1-bit (epub1t)" -ForegroundColor White
    Write-Host " [2] Dọn dẹp sạch file rác macOS (._*)" -ForegroundColor White
    Write-Host " [3] Mở file báo cáo health_report.md" -ForegroundColor White
    Write-Host " [4] Chạy lại kiểm tra (Re-scan)" -ForegroundColor White
    Write-Host " [0] Thoát" -ForegroundColor White
    
    $choice = Read-Host "Nhập lựa chọn của bạn (0-4)"
    switch ($choice) {
        "1" {
            Write-Host "`n[+] Đang khởi chạy tự động convert PDF scan sang EPUB 1-bit monochrome..." -ForegroundColor Yellow
            python $ScriptPath --path "$CurrentFolder" --report "$ReportMd" --json "$ReportJson" --batch-convert-scans
        }
        "2" {
            Write-Host "`n[+] Đang xóa file rác macOS AppleDouble (._*)..." -ForegroundColor Yellow
            python $ScriptPath --path "$CurrentFolder" --clean-junk --no-pdf-inspect
            Write-Host "Đã dọn dẹp sạch sẽ!" -ForegroundColor Green
        }
        "3" {
            if (Test-Path $ReportMd) {
                Invoke-Item $ReportMd
            }
        }
        "4" {
            Write-Host "`n[+] Đang quét lại thư mục $CurrentFolder..." -ForegroundColor Cyan
            python $ScriptPath --path "$CurrentFolder" --report "$ReportMd" --json "$ReportJson"
            $JsonContent = ConvertFrom-Json (Get-Content $ReportJson -Raw -Encoding UTF8)
            $Summary = $JsonContent.summary
            Write-Host "Quét xong! Cập nhật: EPUB=$($Summary.total_epubs), PDF chưa convert=$($Summary.unconverted_pdfs)" -ForegroundColor Green
        }
        "0" {
            Write-Host "`nThoát chương trình. Tạm biệt!" -ForegroundColor Gray
            return
        }
        default {
            Write-Host "Lựa chọn không hợp lệ." -ForegroundColor Red
        }
    }
}
