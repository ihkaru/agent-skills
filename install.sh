#!/usr/bin/env bash
# ==============================================================================
# Agent Skills & Tools Universal Installer (Zero-Friction Bootstrap)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_CONFIG_DIR="${HOME}/.gemini/config"
TARGET_SKILLS_DIR="${TARGET_CONFIG_DIR}/skills"
TARGET_BIN_DIR="${HOME}/.local/bin"

echo "🚀 Initializing Agent Skills & Tools bootstrap..."

# 1. Create target directories
mkdir -p "${TARGET_SKILLS_DIR}"
mkdir -p "${TARGET_BIN_DIR}"

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

# 3. Link all Skills dynamically
echo "🛠️  Setting up skills..."
for skill_path in "${SCRIPT_DIR}"/skills/*; do
    if [ -d "${skill_path}" ]; then
        skill_name="$(basename "${skill_path}")"
        skill_target="${TARGET_SKILLS_DIR}/${skill_name}"
        rm -rf "${skill_target}"
        ln -sf "${skill_path}" "${skill_target}"
        echo "  ✅ Symlinked skill: ${skill_name} -> ${skill_target}"
        
        # Make python and shell scripts executable
        chmod +x "${skill_path}"/scripts/*.py "${skill_path}"/scripts/*.sh 2>/dev/null || true
    fi
done

# 4. Install Global CLI Tool Symlinks to ~/.local/bin
echo "⚡ Installing global CLI tool commands into ~/.local/bin..."
mkdir -p "${TARGET_BIN_DIR}"

# coolify-control
if [ -f "${SCRIPT_DIR}/skills/thinkstation-coolify/scripts/coolify_control.py" ]; then
    ln -sf "${SCRIPT_DIR}/skills/thinkstation-coolify/scripts/coolify_control.py" "${TARGET_BIN_DIR}/coolify-control"
    echo "  ✅ Command: coolify-control"
fi

# static-srp-analyzer
if [ -f "${SCRIPT_DIR}/skills/craftsman-coder/scripts/static_srp_analyzer.py" ]; then
    ln -sf "${SCRIPT_DIR}/skills/craftsman-coder/scripts/static_srp_analyzer.py" "${TARGET_BIN_DIR}/static-srp-analyzer"
    echo "  ✅ Command: static-srp-analyzer"
fi

# codegraph-impact
if [ -f "${SCRIPT_DIR}/skills/craftsman-coder/scripts/codegraph_impact.py" ]; then
    ln -sf "${SCRIPT_DIR}/skills/craftsman-coder/scripts/codegraph_impact.py" "${TARGET_BIN_DIR}/codegraph-impact"
    echo "  ✅ Command: codegraph-impact"
fi

# vsa-boundary-checker
if [ -f "${SCRIPT_DIR}/skills/craftsman-coder/scripts/vsa_boundary_checker.py" ]; then
    ln -sf "${SCRIPT_DIR}/skills/craftsman-coder/scripts/vsa_boundary_checker.py" "${TARGET_BIN_DIR}/vsa-boundary-checker"
    echo "  ✅ Command: vsa-boundary-checker"
fi

# 5. Run Verification Gauntlet
echo "🧪 Running verification tests..."
python3 "${SCRIPT_DIR}/skills/craftsman-coder/scripts/test_codegraph_impact.py"
python3 "${SCRIPT_DIR}/skills/craftsman-coder/scripts/test_static_srp_analyzer.py"
python3 "${SCRIPT_DIR}/skills/craftsman-coder/scripts/test_vsa_boundary_checker.py"
if [ -f "${SCRIPT_DIR}/skills/thinkstation-coolify/scripts/test_coolify_control.py" ]; then
    python3 "${SCRIPT_DIR}/skills/thinkstation-coolify/scripts/test_coolify_control.py"
fi

echo ""
echo "================================================================="
echo "🎉 Agent Skills & Tools bootstrap successfully completed!"
echo "Global rules, skills, and CLI tools are active in AGY CLI & terminal."
echo "================================================================="
