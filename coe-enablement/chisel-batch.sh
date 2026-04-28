#!/usr/bin/env bash
# Chisel batch script: Add observability instrumentation to all TraderX service modules
#
# Iterates over each service module in traderx-monolith/app/services/ and invokes
# the add-observability-to-service skill via Chisel to add structured logging,
# health checks, and request timing.
#
# Usage: ./chisel-batch.sh [--dry-run]
#
# Prerequisites:
#   - Chisel CLI installed and authenticated
#   - traderx-monolith/requirements.txt installed
#   - All existing tests passing

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MONOLITH_DIR="${REPO_ROOT}/traderx-monolith"
SKILL_PATH=".windsurf/skills/add-observability-to-service/SKILL.md"
DRY_RUN="${1:-}"

# Service modules to instrument (from TARGET_ARCHITECTURE_CONSTRAINTS.md §7)
SERVICES=(
  "account_service"
  "trade_processor"
  "people_service"
  # Add new services here as they are extracted:
  # "position_service"
  # "reference_data_service"
  # "notification_service"
)

# Corresponding route modules (for endpoint-level instrumentation)
ROUTE_MODULES=(
  "accounts"
  "trades"
  "people"
  # "positions"
  # "reference_data"
)

echo "============================================"
echo "TraderX Observability Batch Instrumentation"
echo "============================================"
echo "Repo root:  ${REPO_ROOT}"
echo "Skill:      ${SKILL_PATH}"
echo "Services:   ${#SERVICES[@]}"
echo ""

# Step 0: Verify baseline tests pass
echo "[0/$(( ${#SERVICES[@]} + 1 ))] Verifying baseline tests..."
if [[ "${DRY_RUN}" == "--dry-run" ]]; then
  echo "  [DRY RUN] Would run: cd ${MONOLITH_DIR} && python -m pytest tests/ -v"
else
  (cd "${MONOLITH_DIR}" && python -m pytest tests/ -v --tb=short) || {
    echo "ERROR: Baseline tests failing. Fix before running batch instrumentation."
    exit 1
  }
fi
echo ""

# Step 1: Instrument each service module
PASS=0
FAIL=0
SKIP=0
RESULTS=()

for i in "${!SERVICES[@]}"; do
  SERVICE="${SERVICES[$i]}"
  SERVICE_FILE="${MONOLITH_DIR}/app/services/${SERVICE}.py"
  STEP_NUM=$(( i + 1 ))

  echo "[${STEP_NUM}/${#SERVICES[@]}] Instrumenting: ${SERVICE}"

  # Check if service file exists
  if [[ ! -f "${SERVICE_FILE}" ]]; then
    echo "  SKIP: ${SERVICE_FILE} not found"
    RESULTS+=("${SERVICE}: SKIPPED (file not found)")
    SKIP=$(( SKIP + 1 ))
    continue
  fi

  # Check if already instrumented (has structured logging import)
  if grep -q "from app.utils.logging_config import get_logger" "${SERVICE_FILE}" 2>/dev/null; then
    echo "  SKIP: ${SERVICE} already instrumented"
    RESULTS+=("${SERVICE}: SKIPPED (already instrumented)")
    SKIP=$(( SKIP + 1 ))
    continue
  fi

  if [[ "${DRY_RUN}" == "--dry-run" ]]; then
    echo "  [DRY RUN] Would invoke chisel with skill: ${SKILL_PATH}"
    echo "  [DRY RUN] Target: ${SERVICE_FILE}"
    RESULTS+=("${SERVICE}: DRY RUN")
    continue
  fi

  # Invoke Chisel with the observability skill
  PROMPT="Use the add-observability-to-service skill at ${SKILL_PATH} to add \
structured logging, correlation ID support, and request timing to the \
${SERVICE} module at app/services/${SERVICE}.py. \
Convert all existing logger.info/warning/error calls to structured format \
with tenant_id and entity_id fields. Run tests to verify nothing breaks."

  echo "  Invoking Chisel for ${SERVICE}..."
  if chisel run \
    --repo "${REPO_ROOT}" \
    --skill "${SKILL_PATH}" \
    --prompt "${PROMPT}" \
    --wait; then
    echo "  PASS: ${SERVICE} instrumented successfully"
    RESULTS+=("${SERVICE}: PASS")
    PASS=$(( PASS + 1 ))
  else
    echo "  FAIL: ${SERVICE} instrumentation failed"
    RESULTS+=("${SERVICE}: FAIL")
    FAIL=$(( FAIL + 1 ))
  fi

  echo ""
done

# Step 2: Final validation — run full test suite
echo ""
echo "[Final] Running full test suite..."
if [[ "${DRY_RUN}" != "--dry-run" ]]; then
  (cd "${MONOLITH_DIR}" && python -m pytest tests/ -v --tb=short) || {
    echo "WARNING: Some tests failing after instrumentation. Review changes."
    FAIL=$(( FAIL + 1 ))
  }
fi

# Summary
echo ""
echo "============================================"
echo "Batch Instrumentation Summary"
echo "============================================"
for result in "${RESULTS[@]}"; do
  echo "  ${result}"
done
echo ""
echo "Total: ${#SERVICES[@]} services"
echo "  Pass: ${PASS}"
echo "  Fail: ${FAIL}"
echo "  Skip: ${SKIP}"
echo ""

if [[ ${FAIL} -gt 0 ]]; then
  echo "ACTION REQUIRED: ${FAIL} service(s) failed instrumentation. Review logs above."
  exit 1
else
  echo "All services processed successfully."
fi
