#!/bin/bash

set -eo pipefail

finish_without_blocking_launch() {
    local status="$?"

    trap - EXIT
    if ((status != 0)); then
        echo "WARNING: setup.sh exited unexpectedly with status ${status}; continuing session launch"
    fi
    exit 0
}

# Renku exec.d scripts must not prevent the session from launching when an
# optional tool or service cannot be configured.
trap finish_without_blocking_launch EXIT

SSH_FOLDER="${HOME}/.ssh"
KEYS_FOLDER="${RENKU_MOUNT_DIR}/.keys"
BIN_FOLDER="${RENKU_MOUNT_DIR}/.local/bin"
PI_AGENT_DIR="${RENKU_WORKING_DIR}/.pi/agent"
export PATH="${BIN_FOLDER}:${PATH}"

append_bashrc_line() {
    local line="$1"
    grep -Fqx "${line}" "${HOME}/.bashrc" 2>/dev/null || echo "${line}" >> "${HOME}/.bashrc"
}

write_ssh_environment() {
    local environment_file="${SSH_FOLDER}/environment"
    local entry name

    : > "${environment_file}"
    while IFS= read -r -d '' entry; do
        name="${entry%%=*}"

        case "${name}" in
            _|PWD|OLDPWD|SHLVL|TERM|DISPLAY|SSH_*)
                # sshd must populate connection-specific variables itself.
                continue
                ;;
        esac

        if [[ ! "${name}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
            echo "WARNING: ${name} is not a valid sshd environment name; skipping it"
            continue
        fi
        if [[ "${entry}" == *$'\n'* ]]; then
            echo "WARNING: ${name} contains a newline; not exposing it to SSH sessions"
            continue
        fi
        printf '%s\n' "${entry}" >> "${environment_file}"
    done < <(env -0)
    chmod 600 "${environment_file}"
}

setup_sshd() {
    if [ -z "${RENKU_SECRETS_PATH:-}" ]; then
        echo "WARNING: no Renku secrets mounted; skipping SSH service"
        return 0
    fi
    local host_key_file_secret="${RENKU_SECRETS_PATH}/ssh_host_ed25519_key"
    local host_key_file="${SSH_FOLDER}/ssh_host_ed25519_key"
    local authorized_keys_file="${SSH_FOLDER}/authorized_keys"
    local authorized_keys_file_secret="${RENKU_SECRETS_PATH}/authorized_keys"
    local sshd_config="${SSH_FOLDER}/sshd_config"
    local sshd

    if [ -f "${host_key_file_secret}" ]; then
        cp "${host_key_file_secret}" "${host_key_file}"
        echo "" >> "${host_key_file}"
        chmod 600 "${host_key_file}"
        echo "Using SSH host key from secrets"
    fi

    if [ -f "${authorized_keys_file_secret}" ]; then
        cp "${authorized_keys_file_secret}" "${authorized_keys_file}"
        echo "Populated ${authorized_keys_file} from secrets"
    fi

    cat > "${sshd_config}" <<EOF
Port                          2222
ListenAddress                 127.0.0.1
HostKey                       ${host_key_file}
AuthorizedKeysFile            ${authorized_keys_file}
KbdInteractiveAuthentication  no
UsePAM                        yes
X11Forwarding                 yes
PrintMotd                     no
AcceptEnv                     LANG LC_*
PidFile                       /home/renku/sshd.pid
PermitRootLogin               no
PasswordAuthentication        no
AllowTcpForwarding            yes
AllowStreamLocalForwarding    yes
PermitUserEnvironment         yes
Subsystem                     sftp internal-sftp
EOF
    write_ssh_environment
    chmod 600 "${sshd_config}"

    sshd="$(command -v sshd)"
    "${sshd}" -f "${sshd_config}" -E /tmp/sshd.log
    echo "Started sshd daemon"
}

setup_iroh_ssh() {
    local iroh_ssh_bin="${BIN_FOLDER}/iroh-ssh"
    local iroh_ssh_version="0.2.11"
    local iroh_ssh_sha256="4be1091181b04d73625299fe91907004095bcd0ba200c0c6779b065aa3abae2c"
    local private_key="${SSH_FOLDER}/irohssh_ed25519"
    local public_key="${SSH_FOLDER}/irohssh_ed25519.pub"
    local private_key_secret="${RENKU_SECRETS_PATH:-/nonexistent}/irohssh_ed25519"
    local public_key_secret="${RENKU_SECRETS_PATH:-/nonexistent}/irohssh_ed25519.pub"

    if [ -x "${iroh_ssh_bin}" ]; then
        echo "Executable ${iroh_ssh_bin} already present, skipping download"
    else
        curl -fsSL -o "${iroh_ssh_bin}" \
            "https://github.com/rustonbsd/iroh-ssh/releases/download/${iroh_ssh_version}/iroh-ssh.linux"
        chmod +x "${iroh_ssh_bin}"
        echo "Downloaded iroh-ssh ${iroh_ssh_version} to ${iroh_ssh_bin}"
    fi

    echo "${iroh_ssh_sha256}  ${iroh_ssh_bin}" | sha256sum --check -
    echo "iroh-ssh SHA256 verified"

    if [ -f "${private_key_secret}" ] && [ -f "${public_key_secret}" ]; then
        cp "${private_key_secret}" "${private_key}"
        cp "${public_key_secret}" "${public_key}"
        chmod 600 "${private_key}" "${public_key}"
        echo "Using persistent iroh-ssh keys from secrets"
    fi

    start-stop-daemon --start --background \
        --exec "${iroh_ssh_bin}" -- server --ssh-port 2222 --persist
    echo "Started iroh-ssh server"
}

setup_node_tools() {
    local -a packages=()

    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
    # shellcheck source=/dev/null
    . "${HOME}/.nvm/nvm.sh"
    nvm install 24

    command -v pi >/dev/null 2>&1 || packages+=("@earendil-works/pi-coding-agent")
    command -v claude >/dev/null 2>&1 || packages+=("@anthropic-ai/claude-code")
    command -v codex >/dev/null 2>&1 || packages+=("@openai/codex")

    if ((${#packages[@]})); then
        echo "Installing missing coding agents: ${packages[*]}"
        npm install -g "${packages[@]}"
    else
        echo "Coding agents already installed"
    fi
}

# rnk is a Rust binary, independent of the benchmark's Python environment.
setup_renku_cli() (
    local version="0.7.2"
    local arch archive_dir
    if [ -x "${BIN_FOLDER}/rnk" ]; then
        echo "Renku CLI already installed"
        exit 0
    fi
    case "$(uname -m)" in
        x86_64|aarch64) arch="$(uname -m)" ;;
        *) echo "WARNING: unsupported Renku CLI architecture"; exit 1 ;;
    esac
    archive_dir="$(mktemp -d)"
    trap 'rm -rf "${archive_dir}"' EXIT
    curl -fsSL --retry 3 -o "${archive_dir}/rnk.tar.gz" \
        "https://github.com/SwissDataScienceCenter/renku-cli/releases/download/v${version}/rnk-${arch}-unknown-linux-musl-v${version}.tar.gz"
    tar -xzf "${archive_dir}/rnk.tar.gz" -C "${archive_dir}"
    install -m 755 "${archive_dir}/rnk" "${BIN_FOLDER}/rnk"
    "${BIN_FOLDER}/rnk" --help >/dev/null
    echo "Installed Renku CLI ${version}"
)

setup_agent_configuration() {
    local sdsc_llm_source="/workspace/source/sdsc-llm.ts"
    local extension_dir="${PI_AGENT_DIR}/extensions"

    mkdir -p "${extension_dir}" "${RENKU_WORKING_DIR}/.codex" "${RENKU_WORKING_DIR}/.claude"
    if [ -f "${sdsc_llm_source}" ]; then
        cp "${sdsc_llm_source}" "${extension_dir}/"
        echo "Setup pi coding agent SDSC LLM extension from ${sdsc_llm_source}"
    else
        echo "WARNING: sdsc-llm.ts not found, pi coding agent will use default configuration"
    fi

    append_bashrc_line 'export PATH="$RENKU_WORKING_DIR/.local/bin:$PATH"'
    append_bashrc_line 'export PI_CODING_AGENT_DIR=/home/renku/work/.pi/agent'
    append_bashrc_line 'export CLAUDE_CONFIG_DIR=/home/renku/work/.claude'
    append_bashrc_line 'export CODEX_HOME=/home/renku/work/.codex'
    append_bashrc_line 'export BROWSER=true'
}

mkdir -p "${SSH_FOLDER}" "${KEYS_FOLDER}" "${BIN_FOLDER}"
chmod 700 "${SSH_FOLDER}" "${KEYS_FOLDER}"

# Start the local SSH service before the longer independent setup tasks.
setup_sshd &
sshd_pid="$!"
if wait "${sshd_pid}"; then
    echo "Completed sshd setup"
else
    echo "WARNING: sshd setup failed; continuing session launch"
fi

task_names=("iroh-ssh" "Node tools" "Renku CLI")
task_pids=()

setup_iroh_ssh &
task_pids+=("$!")
setup_node_tools &
task_pids+=("$!")
setup_renku_cli &
task_pids+=("$!")

for index in "${!task_pids[@]}"; do
    if wait "${task_pids[index]}"; then
        echo "Completed ${task_names[index]} setup"
    else
        echo "WARNING: ${task_names[index]} setup failed; continuing session launch"
    fi
done

# Run after the NVM installer has finished updating shell configuration.
setup_agent_configuration &
agent_config_pid="$!"
if wait "${agent_config_pid}"; then
    echo "Completed agent configuration"
else
    echo "WARNING: agent configuration failed; continuing session launch"
fi

exit 0
