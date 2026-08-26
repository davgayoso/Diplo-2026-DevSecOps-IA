# Propuesta del Trabajo Final Integrador

## Nombre del proyecto

OWASP LLM Top 10 RAG API.

## Problema y objetivo

El OWASP Top 10 para aplicaciones con modelos de lenguaje reúne riesgos, escenarios de ataque y recomendaciones de mitigación relevantes para el desarrollo seguro de sistemas con inteligencia artificial. Sin embargo, localizar una respuesta concreta dentro del documento completo puede resultar lento para una persona que recién se introduce en el tema.

El proyecto propone construir una API HTTP que responda preguntas sobre el OWASP Top 10 for LLM Applications 2026 mediante Retrieval-Augmented Generation (RAG). La respuesta deberá utilizar únicamente fragmentos recuperados del documento oficial, reconocer cuando la información no está disponible y citar las páginas empleadas como fuente.

## Dominio

El dominio se limita al contenido del documento OWASP Top 10 for LLM Applications 2026. No se incorporarán documentos ajenos a esta publicación ni conocimiento general de ciberseguridad como fuente de las respuestas.

## Funcionalidades previstas

- Ingestión y fragmentación del PDF oficial de OWASP.
- Generación local de embeddings y almacenamiento en un índice FAISS.
- Recuperación de los fragmentos más relevantes para cada pregunta.
- Generación local de respuestas mediante un modelo ejecutado con Ollama.
- Inclusión de fuentes y páginas en cada respuesta.
- Autenticación y autorización por roles para los endpoints protegidos.
- Rate limiting para controlar abuso y consumo de recursos.
- Validación de entradas, salidas y mitigaciones básicas contra prompt injection.
- Logs estructurados y métricas técnicas sin registrar información sensible.
- Ejecución local reproducible mediante Docker Compose.

## Arquitectura y tecnologías

- Python y FastAPI para la API HTTP.
- Ollama como servicio local de modelos.
- Llama 3.2 3B para generación de respuestas.
- Qwen3 Embedding 0.6B para embeddings multilingües.
- FAISS como almacén vectorial embebido.
- Docker y Docker Compose para empaquetado y ejecución local.
- Pytest y Ruff para pruebas y calidad de código.
- GitHub Actions para integración continua.

## Seguridad

El sistema tratará como no confiables la pregunta del usuario, los documentos recuperados y la salida del modelo. Se aplicarán controles deterministas fuera del LLM: validación de esquemas, límites de tamaño y consumo, separación entre instrucciones y contexto, control de acceso, redacción de logs y validación de respuestas. Las amenazas y mitigaciones se documentarán mediante STRIDE.

## Fuera de alcance

No se desarrollará frontend, infraestructura cloud, fine-tuning, alta disponibilidad, multi-tenancy ni ejecución autónoma de herramientas. La API se probará mediante Swagger o curl y todos sus componentes se ejecutarán localmente.

## Fuente documental

OWASP Top 10 for LLM Applications 2026, publicado por OWASP GenAI Security Project bajo licencia Creative Commons Attribution-ShareAlike 4.0. El repositorio conservará el documento sin modificaciones e incluirá la atribución correspondiente.
