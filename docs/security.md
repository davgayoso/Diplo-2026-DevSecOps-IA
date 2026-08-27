# Controles de seguridad

## Autenticacion y secretos

- `/ask` requiere una clave `reader` o `admin` en `X-API-Key`.
- `/metrics` requiere el rol `admin`.
- Las comparaciones usan `secrets.compare_digest`.
- Las claves deben ser distintas y tener al menos 16 caracteres.
- `.env` esta ignorado por Git y no se copia a la imagen.

Las claves de ejemplo nunca deben reutilizarse. Para una demostracion local pueden generarse
con `[guid]::NewGuid().ToString("N")` en PowerShell.

## Entradas, contexto y salidas

- La pregunta tiene entre 3 y 1000 caracteres.
- Unicode se normaliza y se rechazan controles invisibles.
- Se bloquean overrides evidentes sin impedir preguntas educativas sobre prompt injection.
- Los fragmentos se presentan al modelo como datos no confiables y separados de la pregunta.
- La salida debe contener entre 1 y 8000 caracteres y no puede incluir controles invisibles.
- Las fuentes no son generadas por el modelo: proceden de los metadatos del indice.
- La salida se devuelve como JSON y nunca se ejecuta ni interpreta como codigo.

## Contencion y disponibilidad

- Rate limiting por credencial con `429` y `Retry-After`.
- Limites de contexto, tokens de salida y timeouts para Ollama.
- Contenedor de API no root, sin capacidades Linux y con filesystem de solo lectura.
- `no-new-privileges`, `pids_limit` y directorio temporal en memoria.
- El indice se monta de solo lectura en la API.
- El puerto se publica solo en la interfaz local `127.0.0.1`.
- Los logs rotan para evitar crecimiento indefinido.
- Todas las respuestas incluyen `X-Content-Type-Options: nosniff` y
  `Cross-Origin-Resource-Policy: same-origin`.
- `Cache-Control: no-store` evita almacenar respuestas en caches intermedios o del navegador.

## Observabilidad segura

Cada solicitud genera un log JSON con `request_id`, metodo, ruta, estado, duracion, cliente y
rol. Nunca se registran API keys, preguntas, respuestas ni fragmentos recuperados. `/metrics`
expone contadores de solicitudes, latencia y bloqueos, protegido por el rol administrador.

## Cadena de suministro

GitHub Actions ejecuta tests, cobertura, Ruff, Bandit, pip-audit y build del contenedor. Las
dependencias directas y las acciones se fijan a versiones. La imagen de Ollama tambien usa una
version explicita.

## Limitaciones conocidas

- Los filtros de prompt injection son defensa en profundidad, no una garantia.
- API keys estaticas no reemplazan OAuth/OIDC ni la identidad individual.
- El rate limiter en memoria no sirve para replicas multiples.
- No hay TLS porque la API se limita a localhost.
- La primera descarga confia en Docker Hub y el registro de modelos de Ollama.
- Un administrador del host conserva control total sobre contenedores y volumenes.
