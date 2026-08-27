# OWASP LLM Top 10 RAG API

API local para consultar el documento OWASP Top 10 for LLM Applications 2026 mediante Retrieval-Augmented Generation (RAG).

## Estado actual

Hito 3: API RAG local con seguridad, observabilidad y pipeline de integración continua.

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

## Próximos pasos

- Documentar el modelo de amenazas STRIDE y las decisiones de seguridad.
- Completar la revisión final y preparar la defensa.
