# OWASP LLM Top 10 RAG API

API local para consultar el documento OWASP Top 10 for LLM Applications 2026 mediante Retrieval-Augmented Generation (RAG).

## Estado actual

Hito 1: API, ingestión del PDF, embeddings, recuperación FAISS y generación local mediante Ollama.

## Requisitos

- Git.
- Docker Desktop con Docker Compose.
- Al menos 8 GB de RAM; se recomiendan 16 GB.
- Aproximadamente 12 GB de espacio libre para imágenes y modelos.

## Ejecución local

Desde la raíz del repositorio:

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

## Documentación

- [Propuesta y alcance](docs/proposal.md)
- [Atribución del corpus](docs/attribution.md)

## Próximos pasos

- Agregar seguridad, observabilidad, pruebas y CI/CD.
