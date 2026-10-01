# Print candidate Compose v2 plugin executables without invoking Docker.
docker_compose_cli_plugin_paths() {
  local config_file="${DOCKER_CONFIG:-$HOME/.docker}/config.json"
  local dir in_extra line

  print -r -- "${DOCKER_CONFIG:-$HOME/.docker}/cli-plugins/docker-compose"
  [[ -r "$config_file" ]] || return 0

  while IFS= read -r line; do
    if [[ "$line" == *'"cliPluginsExtraDirs"'* ]]; then
      in_extra=1
      line="${line#*\"cliPluginsExtraDirs\"}"
    fi
    (( in_extra )) || continue

    while [[ "$line" == *'"'* ]]; do
      line="${line#*\"}"
      dir="${line%%\"*}"
      line="${line#*\"}"
      [[ -n "$dir" ]] && print -r -- "$dir/docker-compose"
    done
    [[ "$line" == *']'* ]] && break
  done < "$config_file"
}

# Return success when a Compose v2 plugin executable is discoverable.
has_docker_compose_cli_plugin() {
  local plugin
  while IFS= read -r plugin; do
    [[ -x "$plugin" ]] && return 0
  done < <(docker_compose_cli_plugin_paths)

  for plugin in \
    "/usr/local/lib/docker/cli-plugins/docker-compose" \
    "/usr/local/libexec/docker/cli-plugins/docker-compose" \
    "/usr/lib/docker/cli-plugins/docker-compose" \
    "/usr/libexec/docker/cli-plugins/docker-compose"; do
    [[ -x "$plugin" ]] && return 0
  done
  return 1
}
