# NanoJuris frontend

The React/Vite frontend exposes the official NanoJuris Studio Workbench:

- `/`: official NanoJuris Studio;
- `/studio`: official Studio route;
- `/workbench`: compatibility alias.

## Development

```powershell
npm ci
$env:VITE_DATA_MODE="mock"
npm run dev
```

Use `VITE_DATA_MODE=api` to call the real FastAPI endpoints. Mock mode is
offline and deterministic; API mode preserves real source and error states.

## Build

```powershell
npm run typecheck
npm run build
```

The build generates the static bundle consumed by `nanojuris studio`. Node is a
build-time dependency only. `node_modules` and Deno caches are excluded from
the Python sdist and wheel.

To disable the route at the FastAPI layer without removing its files:

```powershell
$env:NANOJURIS_WORKBENCH_ENABLED="0"
```
