#!/usr/bin/env sh
set -eu

profile_id="${1:?profile id is required}"
bot_token_name="${2:?bot token secret name is required}"
owner_id_name="${3:?owner id secret name is required}"
model_api_key_name="${4:-}"
runtime_root="${EXO_RUNTIME_ROOT:?EXO_RUNTIME_ROOT is required}"
bridge_dir="${runtime_root}/${profile_id}/secret-bridge"

umask 077
mkdir -p "${bridge_dir}"

# This script is intentionally a template. Operators run it under `phase run`
# so profile-specific variables are provided by Phase at process start and
# never by git.
bot_token="$(printenv "${bot_token_name}" || true)"
owner_id="$(printenv "${owner_id_name}" || true)"
model_api_key=""
if [ -n "${model_api_key_name}" ]; then
  model_api_key="$(printenv "${model_api_key_name}" || true)"
fi

missing=""
if [ -z "${bot_token}" ]; then
  missing="${missing} ${bot_token_name}"
fi
if [ -z "${owner_id}" ]; then
  missing="${missing} ${owner_id_name}"
fi
if [ -n "${model_api_key_name}" ] && [ -z "${model_api_key}" ]; then
  missing="${missing} ${model_api_key_name}"
fi

if [ -n "${missing}" ]; then
  printf '%s\n' "missing required Phase-injected secrets:${missing}" >&2
  exit 1
fi

token_file="${bridge_dir}/telegram-bot-token"
token_file_tmp="${token_file}.$$"
provider_env="${bridge_dir}/provider.env"
provider_env_tmp="${provider_env}.$$"
trap 'rm -f "${token_file_tmp}" "${provider_env_tmp}"' EXIT HUP INT TERM
printf '%s' "${bot_token}" > "${token_file_tmp}"
mv "${token_file_tmp}" "${token_file}"

: > "${provider_env_tmp}"
printf 'TELEGRAM_BOT_TOKEN=%s\n' "${bot_token}" >> "${provider_env_tmp}"
printf 'TELEGRAM_ALLOWED_USERS=%s\n' "${owner_id}" >> "${provider_env_tmp}"
printf 'TELEGRAM_HOME_CHANNEL=%s\n' "${owner_id}" >> "${provider_env_tmp}"
if [ -n "${model_api_key_name}" ]; then
  printf '%s=%s\n' "${model_api_key_name}" "${model_api_key}" >> "${provider_env_tmp}"
fi
mv "${provider_env_tmp}" "${provider_env}"

chmod 0600 "${token_file}" 2>/dev/null || true
chmod 0600 "${provider_env}"
