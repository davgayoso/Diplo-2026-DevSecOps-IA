# Lista de verificacion de entrega

## Repositorio

- [ ] `main` contiene todos los pull requests fusionados.
- [ ] GitHub Actions esta en verde sobre el ultimo commit de `main`.
- [ ] El repositorio es publico y abre sin iniciar sesion.
- [ ] No se publico `.env`, una API key ni otro secreto.
- [ ] No hay archivos temporales, caches ni indices generados versionados.

## Ejecucion

- [ ] `Copy-Item .env.example .env` y reemplazo de ambas claves.
- [ ] `docker compose config` finaliza sin errores.
- [ ] `docker compose up --build` inicia los servicios.
- [ ] `/health` responde `200`.
- [ ] `/ready` responde `200` y muestra fragmentos cargados.
- [ ] Una consulta normal en `/ask` responde `200` con fuentes.
- [ ] Una instruccion maliciosa responde `422`.
- [ ] `/metrics` responde `403` para `reader` y `200` para `admin`.

## Calidad y seguridad

- [ ] `ruff check .` finaliza correctamente.
- [ ] `ruff format --check .` finaliza correctamente.
- [ ] `pytest` supera el minimo de cobertura.
- [ ] `bandit --quiet --recursive app` no encuentra problemas.
- [ ] `pip-audit --requirement requirements.txt` no encuentra vulnerabilidades conocidas.

## Documentacion

- [ ] README con instalacion, ejecucion, pruebas y alternativas de hardware.
- [ ] Propuesta y atribucion del corpus.
- [ ] Arquitectura y decisiones tecnicas.
- [ ] Modelo STRIDE con riesgo residual.
- [ ] Controles y limitaciones de seguridad.
- [ ] Guion de defensa revisado.

## Entrega

- [ ] Copiar el enlace publico exacto del repositorio.
- [ ] Enviar el enlace por el medio indicado en la consigna antes del cierre.
- [ ] Abrir el enlace enviado para verificar que no este roto.
- [ ] Conservar una copia local de `.env` para la demostracion.
- [ ] Probar la demostracion completa antes de la defensa.
