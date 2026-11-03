param(
  [string]$ComfyRoot = $env:COMFYUI_ROOT
)

$ErrorActionPreference = "Stop"

if (-not $ComfyRoot) {
  $ComfyRoot = "D:\AI\ComfyUI"
}

$Python = Join-Path $ComfyRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
  throw "ComfyUI virtual-environment Python not found: $Python"
}

Write-Host "Checking current PyTorch CUDA runtime..."
$CudaVersion = & $Python -c "import torch; print(torch.version.cuda or '')" 2>$null
if ($LASTEXITCODE -ne 0 -or $CudaVersion.Trim() -ne "12.6") {
  Write-Host "Installing the verified CUDA 12.6 PyTorch runtime..."
  & $Python -m pip install --upgrade --force-reinstall torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu126
  if ($LASTEXITCODE -ne 0) {
    throw "PyTorch CUDA package installation failed."
  }
}

Write-Host "Running a CUDA device and kernel test..."
& $Python -c "import torch; assert torch.cuda.is_available(), 'CUDA is not available'; a=torch.randn((512,512),device='cuda'); b=a@a; torch.cuda.synchronize(); print('PyTorch:',torch.__version__); print('CUDA runtime:',torch.version.cuda); print('GPU:',torch.cuda.get_device_name(0)); print('Kernel test:',bool(torch.isfinite(b).all().item()))"
if ($LASTEXITCODE -ne 0) {
  throw "CUDA verification failed. Check the NVIDIA driver and GPU compatibility."
}

Write-Host "CUDA-enabled PyTorch is ready. Start ComfyUI with --lowvram for GPUs with limited VRAM."
