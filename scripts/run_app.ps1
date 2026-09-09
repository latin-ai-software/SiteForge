# PowerShell script to run the main app with UTF-8 encoding

$env:PYTHONIOENCODING = 'utf-8'

Write-Host "🚀 Starting Latin Magazine Application..." -ForegroundColor Green
Write-Host "Opening http://localhost:443 in your browser..." -ForegroundColor Cyan
Write-Host ""

# Open browser automatically (after a short delay to let server start)
Start-Sleep -Seconds 3
Start-Process "https://localhost:443" -ErrorAction SilentlyContinue

# Run the Flask app with arguments
python app.py @args
