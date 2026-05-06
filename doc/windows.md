# Windows support (experimental)

openfortivpn is primarily developed for Unix-like systems. This repository now
includes an **experimental Windows launcher UI** that offers a more modern UX
for starting and stopping VPN sessions.

## What is included

- `contrib/windows/OpenFortiVpn.Ui.ps1`: a PowerShell + WPF desktop UI.
- A simple workflow to start `openfortivpn -c <config>` and stream logs.

## Requirements

1. Windows 10/11 with PowerShell 5.1+.
2. `openfortivpn` executable available in `PATH` (for example via WSL wrapper,
   MSYS2, or a custom build).
3. A working openfortivpn configuration file.

## Run

```powershell
powershell -ExecutionPolicy Bypass -File .\contrib\windows\OpenFortiVpn.Ui.ps1
```

## Notes

- This UI is intentionally lightweight and does not replace VPN stack details.
- Advanced routing, DNS, and privilege behavior still depend on how
  `openfortivpn` is provided on Windows.
