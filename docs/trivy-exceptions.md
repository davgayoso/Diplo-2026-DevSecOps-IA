# Excepciones temporales de Trivy

## Decisión

El responsable del proyecto autorizó aceptar temporalmente los hallazgos
indicados en `security/trivy-exceptions.json` para la entrega local.
No se cambia Debian, Docker Compose, Ollama ni el funcionamiento del RAG.
No se afirma que esas vulnerabilidades estén corregidas ni que sean falsos positivos.

Vigencia: desde el 31 de agosto de 2026 hasta antes del **14 de septiembre de 2026,
00:00 UTC**. El vencimiento no se renueva automáticamente.

El alcance es Debian 13.6, arquitectura amd64, paquetes del sistema operativo
y versiones exactas. Son 16 combinaciones CVE/paquete (13 CVE distintos):
13 hallazgos HIGH y 3 CRITICAL. No se aceptan automáticamente hallazgos de Python,
de otras imágenes como Ollama, ni hallazgos nuevos sin parche.

## Integración: cuatro archivos y un paso del workflow

Copiar `scripts/`, `security/`, `tests/` y `docs/` del ZIP a la raíz del
repositorio, combinando las carpetas existentes. Solo se agregan estos archivos:

- `scripts/check_trivy.py`
- `security/trivy-exceptions.json`
- `tests/test_trivy_policy.py`
- `docs/trivy-exceptions.md`

En `.github/workflows/ci.yaml`, buscar el paso FINAL que ejecuta:

```yaml
run: trivy convert --format table --severity HIGH,CRITICAL --exit-code 1 trivy-report.json
```

Reemplazar ese paso completo (su `name` y `run`) por el siguiente, conservando
la misma indentación que los otros pasos del job `container`:

```yaml
      - name: Enforce Trivy policy with temporary exceptions
        run: |
          python3 -m unittest discover -s tests -p "test_trivy_policy.py" -v
          python3 scripts/check_trivy.py trivy-report.json
```

No mantener el bloqueo anterior además del nuevo: seguiría rechazando las
excepciones. No agregar `continue-on-error`, `|| true`, `--ignore-unfixed`,
`--ignore-status`, `--ignore-policy` ni una lista global de CVE ignorados.

El paso previo de análisis debe conservar la generación del **reporte completo**:

```yaml
      - name: Scan API image with Trivy
        run: |
          trivy --version
          trivy image \
            --image-src docker \
            --scanners vuln \
            --severity UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL \
            --format json \
            --output trivy-report.json \
            --exit-code 0 \
            --timeout 10m \
            owasp-llm-rag-api:ci
          trivy convert --format table --output trivy-report.txt trivy-report.json
```

Aquí `--exit-code 0` permite guardar el reporte aunque haya vulnerabilidades;
**el paso siguiente decide si CI falla**. Un error de ejecución del escáner
no debe ocultarse. Conservar la subida de JSON y TXT como artefactos antes
del nuevo control, o con `if: always()`.

No aplicar filtros ni variables `TRIVY_*` de supresión al reporte de entrada.
El verificador necesita el JSON completo; no puede recuperar hallazgos que
un escaneo previo haya descartado. No requiere pip ni dependencias adicionales:
se ejecuta con Python del runner, no con Python del contenedor.

## Validación local, sin reconstruir Docker

Desde PowerShell, en la raíz del repositorio:

```powershell
python -m unittest discover -s tests -p "test_trivy_policy.py" -v
python scripts/check_trivy.py "C:\ruta\al\trivy-report(1).json"
$LASTEXITCODE
```

Reemplazar la ruta por la ubicación real del JSON ya descargado. Las comillas
son necesarias cuando hay espacios o paréntesis. Se puede arrastrar el archivo
a PowerShell para insertar su ruta.

Para el reporte utilizado para aprobar estas excepciones, durante su vigencia:

```text
Hallazgos totales: 131 | HIGH/CRITICAL: 16
Aceptados temporalmente: 16 | Bloqueantes: 0
...
APROBADO CON RIESGO RESIDUAL: las vulnerabilidades no estan corregidas.
```

El último comando debe mostrar `0`. La cantidad de hallazgos de un escaneo
nuevo puede cambiar. Los códigos de salida son: `0` cumple la política,
`1` hay vulnerabilidades bloqueantes y `2` el reporte o la política es inválido.

Ejecutar también los controles habituales antes de subir:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Crear el commit `security: add scoped expiring Trivy exceptions` y subir la rama.
Si el archivo del workflow tiene otro nombre, editar el que contiene el bloqueo
actual; no crear un workflow paralelo. No se modifica Dockerfile.

## Cuándo vuelve a bloquear

- Aparece un HIGH/CRITICAL sin coincidencia exacta en la lista.
- Trivy informa `FixedVersion`, incluso para una excepción aprobada.
- Cambian el paquete, su versión, severidad, SO o arquitectura para un hallazgo
  que sigue siendo HIGH/CRITICAL.
- Se alcanza el vencimiento y quedan hallazgos que dependían de las excepciones.
- Hay un HIGH/CRITICAL en paquetes de Python.
- El reporte falta, está mal formado o no incluye el análisis de Debian y Python.
- Debian se identifica como fuera de soporte.

Los LOW, MEDIUM y UNKNOWN siguen visibles, pero no bloquean según el umbral
HIGH/CRITICAL que ya usaba el proyecto. Si un hallazgo desaparece después de
actualizar, no se exige conservarlo ni se bloquea por una excepción sin uso.

## Justificación y límites

Se acepta el riesgo únicamente para una demostración local con corpus controlado,
sin subida pública de archivos, sin ejecución de herramientas o código generado,
API enlazada a localhost, usuario sin privilegios, capacidades Linux eliminadas,
`no-new-privileges` y raíz del contenedor de solo lectura.

Las justificaciones describen las rutas que no usa el código revisado: gzip,
infocmp, administración de ACL, SQLite y módulos de Perl. Son argumentos para
priorizar el riesgo, no una prueba formal de ausencia de explotación. El
verificador evalúa metadatos; **no comprueba que Compose conserve esos controles**.
Si se cambia el alcance, se publica la API o se agregan dichas funcionalidades,
se deben revisar las excepciones antes de desplegar.

Responsable: David Gayoso. Antes del vencimiento, reconstruir con imágenes y
paquetes actualizados, volver a escanear y retirar las excepciones resueltas.
Si quedan pendientes, documentar una revisión nueva y su justificación antes de
extender una fecha. El job actual se ejecuta en eventos de GitHub: el vencimiento
se comprueba en la próxima ejecución, no detiene contenedores ya desplegados.

## Explicación para la defensa

"Trivy sigue analizando la imagen completa. Corregí los hallazgos que tenían
solución y acepté temporalmente 16 hallazgos del sistema operativo sin versión
corregida indicada en el reporte. Cada excepción identifica CVE, paquete y
versión; tiene vencimiento y justificación para el alcance local. El control
sigue bloqueando vulnerabilidades nuevas, parches disponibles y excepciones
vencidas. Un resultado verde significa cumplir esta política, no tener cero
vulnerabilidades."

## Verificación del cambio

Antes de entregar este parche se ejecutaron 22 tests unitarios, Ruff check y
Ruff format --check, todos correctos. También se evaluó el JSON real: 131
hallazgos totales, 16 aceptados y 0 bloqueantes. Sobre copias en memoria se
comprobó que quitar las excepciones o alcanzar el vencimiento bloquea los 16;
agregar una vulnerabilidad nueva bloquea esa nueva vulnerabilidad; e informar
una versión corregida para los 16 hace que los 16 vuelvan a bloquear.

Esta verificación no reconstruye la imagen ni ejecuta GitHub Actions. El
resultado de un nuevo escaneo depende de la imagen y la base de vulnerabilidades
vigentes. No se promete que futuras ejecuciones permanezcan verdes.

## Referencias

- [CLI de Trivy convert](https://trivy.dev/docs/latest/references/configuration/cli/trivy_convert/)
- [Filtros y excepciones de Trivy](https://trivy.dev/docs/latest/configuration/filtering/)
- [Debian: CVE-2026-42496](https://security-tracker.debian.org/tracker/CVE-2026-42496)
- [Debian: CVE-2026-11822](https://security-tracker.debian.org/tracker/CVE-2026-11822)

La base de la aceptación es el reporte proporcionado por el responsable,
Trivy 0.74.0, imagen `owasp-llm-rag-api:ci`, Debian 13.6 amd64,
ID `sha256:cb228239c12575e187018fe88e28bb38175a413ec46bbc1db5ffd7f924344b78`.
El verificador no fija ese ID: permite reconstrucciones, pero solo acepta las
combinaciones exactas de la lista mientras cumplan todas las condiciones.
