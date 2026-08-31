"""Apply explicit, temporary exceptions to an unfiltered Trivy image report."""

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

SEVERITIES = {"UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
BLOCKING = {"HIGH", "CRITICAL"}


def evaluate(report, policy, today=None):
    """Return total findings, accepted rows and blocking rows; fail closed on bad input."""
    today = today or datetime.now(UTC).date()
    if not isinstance(report, dict) or not isinstance(policy, dict):
        raise ValueError("El reporte y la politica deben ser objetos JSON.")
    if report.get("SchemaVersion") != 2 or report.get("ArtifactType") != "container_image":
        raise ValueError("Se requiere un reporte Trivy v2 de una imagen de contenedor.")
    if policy.get("schema_version") != 1 or not policy.get("approved_by"):
        raise ValueError("Politica invalida o sin responsable.")
    start = date.fromisoformat(policy["approved_on"])
    expiry = date.fromisoformat(policy["expires_on"])
    if expiry <= start:
        raise ValueError("El vencimiento debe ser posterior a la aprobacion.")
    scope = policy["scope"]
    for field in ("os_family", "os_name", "architecture"):
        if not isinstance(scope[field], str) or not scope[field]:
            raise ValueError("Alcance incompleto en la politica.")
    rules = {}
    if not isinstance(policy["exceptions"], list):
        raise ValueError("Las excepciones deben ser una lista.")
    for entry in policy["exceptions"]:
        fields = ("id", "package", "version", "severity", "reason")
        if any(not isinstance(entry[f], str) or not entry[f].strip() for f in fields):
            raise ValueError("Excepcion incompleta.")
        key = tuple(entry[f] for f in fields[:4])
        if key in rules or entry["severity"] not in BLOCKING:
            raise ValueError("Excepcion duplicada o severidad no permitida.")
        rules[key] = entry["reason"]

    metadata = report["Metadata"]
    actual_scope = {
        "os_family": metadata["OS"]["Family"],
        "os_name": metadata["OS"]["Name"],
        "architecture": metadata["ImageConfig"]["architecture"],
    }
    if metadata["OS"].get("EOSL"):
        raise ValueError("El sistema operativo esta fuera de soporte.")
    results = report["Results"]
    if not isinstance(results, list):
        raise ValueError("Results debe ser una lista.")
    targets = {(r["Class"], r["Type"]) for r in results}
    if not {("os-pkgs", "debian"), ("lang-pkgs", "python-pkg")} <= targets:
        raise ValueError("El reporte debe incluir los analisis de Debian y Python.")

    accepted, blocked = [], []
    total = 0
    for result in results:
        if result.get("ExperimentalModifiedFindings"):
            raise ValueError("El reporte contiene hallazgos suprimidos; generar uno sin filtros.")
        findings = result.get("Vulnerabilities")
        if findings is None:
            findings = []
        if not isinstance(findings, list):
            raise ValueError("Vulnerabilities debe ser una lista o null.")
        for finding in findings:
            fields = ("VulnerabilityID", "PkgName", "InstalledVersion", "Severity")
            if any(not isinstance(finding[f], str) or not finding[f] for f in fields):
                raise ValueError("Hallazgo incompleto.")
            total += 1
            key = tuple(finding[f] for f in fields)
            if key[3] not in SEVERITIES:
                raise ValueError("Severidad desconocida en el reporte.")
            if key[3] not in BLOCKING:
                continue
            label = f"{key[0]} | {key[1]} {key[2]} | {key[3]}"
            if finding.get("FixedVersion"):
                reason = f"Existe correccion: {finding['FixedVersion']}"
            elif actual_scope != scope or result["Class"] != "os-pkgs":
                reason = "Fuera del alcance aprobado (SO, arquitectura o tipo de paquete)."
            elif result["Type"] != scope["os_family"] or key not in rules:
                reason = "CVE, paquete, version o severidad sin excepcion."
            elif not start <= today < expiry:
                reason = f"Excepcion fuera de vigencia; vence {expiry} UTC."
            else:
                accepted.append(f"{label} | {rules[key]}")
                continue
            blocked.append(f"{label} | {reason}")
    return total, accepted, blocked


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--policy", type=Path, default=Path("security/trivy-exceptions.json"))
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8-sig"))
        policy = json.loads(args.policy.read_text(encoding="utf-8-sig"))
        total, accepted, blocked = evaluate(report, policy)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"ERROR: no se pudo validar el reporte o la politica: {exc}", file=sys.stderr)
        return 2
    print(f"Hallazgos totales: {total} | HIGH/CRITICAL: {len(accepted) + len(blocked)}")
    print(f"Aceptados temporalmente: {len(accepted)} | Bloqueantes: {len(blocked)}")
    for row in accepted:
        print(f"ACEPTADO hasta {policy['expires_on']} UTC: {row}")
    for row in blocked:
        print(f"BLOQUEADO: {row}")
    if blocked:
        print("RECHAZADO: revisar los hallazgos bloqueantes.")
        return 1
    if accepted:
        print("APROBADO CON RIESGO RESIDUAL: las vulnerabilidades no estan corregidas.")
    else:
        print("APROBADO: no se detectaron hallazgos HIGH/CRITICAL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
