# NanoJuris frontend

The React/Vite frontend exposes two experiences during the migration:

- `/`: NanoJuris Workbench, the primary interface;
- `/studio`: legacy Studio kept as a compatibility fallback;
- `/workbench`: explicit Workbench route.

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

Set `VITE_WORKBENCH_DEFAULT=0` for a temporary legacy-root transition. The
Workbench remains available at `/workbench` in either mode.

To disable the route at the FastAPI layer without removing its files:

```powershell
$env:NANOJURIS_WORKBENCH_ENABLED="0"
```
