#!/usr/bin/env bash
# ==============================================================================
# Agent Skills & Tools Universal Installer (Zero-Friction Bootstrap)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_CONFIG_DIR="${HOME}/.gemini/config"
TARGET_SKILLS_DIR="${TARGET_CONFIG_DIR}/skills"

echo "🚀 Initializing Agent Skills & Tools bootstrap..."

# 1. Create target directories
mkdir -p "${TARGET_SKILLS_DIR}"

# 2. Deploy configuration files
echo "📦 Deploying global configuration..."
if [ ! -f "${TARGET_CONFIG_DIR}/GEMINI.md" ]; then
    cp "${SCRIPT_DIR}/config/GEMINI.md" "${TARGET_CONFIG_DIR}/GEMINI.md"
    echo "  ✅ Installed ~/.gemini/config/GEMINI.md"
else
    echo "  ℹ️  Existing GEMINI.md found, preserving local config."
fi

cp "${SCRIPT_DIR}/config/skills.json" "${TARGET_CONFIG_DIR}/skills.json"
echo "  ✅ Registered ~/.gemini/config/skills.json"

# 3. Link or Copy Skills
SKILL_TARGET="${TARGET_SKILLS_DIR}/craftsman-coder"
echo "🛠️  Setting up craftsman-coder skill..."
rm -rf "${SKILL_TARGET}"
ln -sf "${SCRIPT_DIR}/skills/craftsman-coder" "${SKILL_TARGET}"
echo "  ✅ Symlinked ${SKILL_TARGET} -> ${SCRIPT_DIR}/skills/craftsman-coder"

# 4. Make scripts executable
chmod +x "${SCRIPT_DIR}"/skills/craftsman-coder/scripts/*.py 2>/dev/null || true

# 5. Run Verification Gauntlet
echo "🧪 Running verification tests..."
python3 "${SCRIPT_DIR}/skills/craftsman-coder/scripts/test_codegraph_impact.py"
python3 "${SCRIPT_DIR}/skills/craftsman-coder/scripts/test_static_srp_analyzer.py"
python3 "${SCRIPT_DIR}/skills/craftsman-coder/scripts/test_vsa_boundary_checker.py"

echo ""
echo "================================================================="
echo "🎉 Agent Skills bootstrap successfully completed!"
echo "Global rules and craftsman-coder skill are active in AGY CLI."
echo "================================================================="
