# Local ComfyUI GPU runtime

This is the local Windows GPU companion to the Thinbi agent. It is not a Render GPU service: the coloring-book endpoints deliberately accept loopback requests only and connect to ComfyUI on this same computer.

## Verified local configuration

The runtime was verified on an NVIDIA GeForce MX230 (2 GB VRAM), NVIDIA driver 582.78, Python 3.13, and PyTorch 2.7.1+cu126. The test ran a CUDA matrix multiplication successfully and ComfyUI reported a CUDA device. Use low-VRAM mode with this GPU.

## Install or repair the CUDA-enabled PyTorch runtime

Open PowerShell and run:

~~~powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup-comfyui-gpu.ps1 -ComfyRoot 'D:\AI\ComfyUI'
~~~

The script installs PyTorch 2.7.1, torchvision 0.22.1, and torchaudio 2.7.1 from the CUDA 12.6 wheel index only when the active ComfyUI environment is not already using CUDA 12.6. It then runs an actual CUDA kernel test. A separate CUDA Toolkit installation is not required for these PyTorch wheels.

## Start ComfyUI

Keep ComfyUI bound to loopback; do not expose its API on the public network.

~~~powershell
Set-Location 'D:\AI\ComfyUI'
.\.venv\Scripts\python.exe main.py --lowvram --listen 127.0.0.1 --port 8188 --output-directory 'D:\Coloring Books\Cozy Christmas Coloring Book'
~~~

Verify the runtime:

~~~powershell
Invoke-RestMethod http://127.0.0.1:8188/system_stats
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
~~~

## Local agent settings

The local agent can use these optional environment variables. Keep the .env file out of source control.

- COMFYUI_URL=http://127.0.0.1:8188
- COLORING_BOOK_ROOT=D:\Coloring Books\Cozy Christmas Coloring Book
- COLORING_BOOK_PYTHON=D:\AI\ComfyUI\.venv\Scripts\python.exe
- COLORING_BOOK_CHECKPOINT=v1-5-pruned-emaonly-fp16.safetensors

The default KDP interior is 100 pages: 50 illustrated fronts and 50 blank backs. The generator and assembler therefore target 50 illustrations, not 100 illustrations. Test-named PNG outputs are excluded from final assembly.

## Resource limits and safety

The MX230 has only 2 GB of VRAM. Keep generation at 512×512 with the low-VRAM ComfyUI mode and review generated line art visually. Automated ink-coverage checks cannot replace page-by-page print QC. The local coloring-book routes reject non-loopback clients, and the ComfyUI URL validator accepts localhost addresses only.
