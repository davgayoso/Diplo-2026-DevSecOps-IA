# OWASP LLM Top 10 RAG API

API local para consultar el documento OWASP Top 10 for LLM Applications 2026 mediante Retrieval-Augmented Generation (RAG).

## Estado actual

Hito 0: estructura inicial, endpoint de salud y ejecución local mediante Docker Compose.

## Requisitos

- Git.
- Docker Desktop con Docker Compose.

## Ejecución local

Desde la raíz del repositorio:

```bash
docker compose up --build
```

Cuando el contenedor esté listo:

- Health check: <http://localhost:8000/health>
- Swagger: <http://localhost:8000/docs>

Para detener el proyecto:

```bash
docker compose down
```

## Documentación

- [Propuesta y alcance](docs/proposal.md)

## Próximos pasos

- Incorporar el documento oficial de OWASP con su atribución.
- Implementar ingestión, embeddings, recuperación y generación local.
- Agregar seguridad, observabilidad, pruebas y CI/CD.
