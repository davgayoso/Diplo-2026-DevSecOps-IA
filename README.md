# OWASP LLM Top 10 RAG API

API local para consultar el documento OWASP Top 10 for LLM Applications 2026 mediante Retrieval-Augmented Generation (RAG).

## Estado actual

Version final: API RAG local con seguridad, observabilidad, CI y modelo de amenazas STRIDE.

## Arquitectura resumida

Docker Compose coordina Ollama, la descarga de modelos, la ingestion del PDF y FastAPI. La
pregunta se transforma en un embedding, FAISS recupera los fragmentos relevantes y Llama 3.2
redacta una respuesta limitada a ese contexto. La lista estructurada de fuentes se construye a
partir del indice y no depende de lo que afirme el modelo.

Las decisiones y sus trade-offs estan detallados en
[Arquitectura y decisiones tecnicas](docs/architecture.md).

## Requisitos

- Git.
- Docker Desktop con Docker Compose.
- Al menos 8 GB de RAM; se recomiendan 16 GB.
- Aproximadamente 12 GB de espacio libre para imágenes y modelos.

## Ejecución local

Creá el archivo local de configuración:

```powershell
Copy-Item .env.example .env
```

Generá dos claves distintas desde PowerShell:

```powershell
[guid]::NewGuid().ToString("N")
[guid]::NewGuid().ToString("N")
```

Reemplazá en `.env` los valores de `READER_API_KEY` y `ADMIN_API_KEY`. El archivo `.env` está ignorado por Git y no debe publicarse.

Después, desde la raíz del repositorio:

```bash
docker compose up --build
```

La primera ejecución descarga los modelos y crea el índice. Puede tardar varios minutos. Las ejecuciones siguientes reutilizan los volúmenes persistentes.

La ingestión utiliza las páginas 5 a 107 del PDF. Se excluyen la portada, la licencia, el índice general, las referencias bibliográficas y los créditos para evitar que esos textos desplacen contenido técnico relevante durante la recuperación.

Cuando el contenedor esté listo:

- Health check: <http://localhost:8000/health>
- Readiness check: <http://localhost:8000/ready>
- Swagger: <http://localhost:8000/docs>

En Swagger, probá `POST /ask` con:

```json
{
  "question": "¿Qué es prompt injection y cómo recomienda OWASP mitigarla?"
}
```

Primero presioná `Authorize` e ingresá una de las claves bajo `X-API-Key`. La clave `reader` permite consultar `/ask`; la clave `admin` también permite consultar `/metrics`.

Las respuestas de error utilizan un formato uniforme e incluyen un identificador de solicitud. Las consultas están limitadas por credencial según `RATE_LIMIT_REQUESTS` y `RATE_LIMIT_WINDOW_SECONDS`.

Ejemplo equivalente mediante PowerShell:

```powershell
$headers = @{ "X-API-Key" = "TU_READER_API_KEY" }
$body = @{ question = "¿Qué es prompt injection y cómo recomienda OWASP mitigarla?" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/ask" -Headers $headers -ContentType "application/json" -Body $body
```

Los logs JSON pueden observarse con:

```bash
docker compose logs -f api
```

El endpoint `/metrics` devuelve métricas Prometheus de solicitudes, latencia y bloqueos por rate limiting. Requiere la clave de administrador.

Para detener el proyecto:

```bash
docker compose down
```

No uses `docker compose down -v` salvo que quieras eliminar los modelos y el índice.

## Equipos con menos recursos

Copiá `.env.example` como `.env` y cambiá:

```dotenv
LLM_MODEL=llama3.2:1b
```

El modelo de 1B reduce el consumo de memoria a cambio de respuestas menos elaboradas.

## Aceleración NVIDIA opcional

La configuración principal funciona por CPU. En Windows con WSL 2, controladores NVIDIA actualizados y soporte GPU de Docker configurado, podés iniciar con:

```bash
docker compose -f compose.yaml -f compose.gpu.yaml up --build
```

## Pruebas y calidad

Instalá las dependencias de desarrollo y ejecutá las mismas verificaciones que utiliza CI:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
ruff check .
ruff format --check .
pytest
bandit --quiet --recursive app
pip-audit --requirement requirements.txt
```

Los tests usan implementaciones simuladas de Ollama, por lo que no descargan modelos ni requieren GPU.

## Documentación

- [Propuesta y alcance](docs/proposal.md)
- [Atribución del corpus](docs/attribution.md)
- [Arquitectura y decisiones técnicas](docs/architecture.md)
- [Modelo de amenazas STRIDE](docs/threat-model.md)
- [Controles y limitaciones de seguridad](docs/security.md)
- [Guion de defensa de 10 minutos](docs/defense.md)
- [Lista de verificación de entrega](docs/delivery-checklist.md)

## Controles principales

- API keys y autorización con roles `reader` y `admin`.
- Rate limiting por credencial con respuesta `429` y `Retry-After`.
- Validación y normalización de entradas y salidas del modelo.
- Separación del contexto no confiable y mitigaciones contra prompt injection.
- Logs JSON sin claves, preguntas, respuestas ni fragmentos.
- Métricas Prometheus restringidas al administrador.
- API ejecutada como usuario no root, sin capacidades, con filesystem de solo lectura.
- Puerto publicado solamente en `127.0.0.1` y Ollama sin puerto público.
- Tests, cobertura, Ruff, Bandit, pip-audit y build ejecutados en GitHub Actions.

Las limitaciones conocidas y el riesgo residual se documentan explícitamente; este proyecto no
se presenta como una solución lista para producción.
