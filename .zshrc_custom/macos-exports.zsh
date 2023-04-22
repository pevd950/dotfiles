# Flutter
export PATH=$PATH:$USER/flutter/bin

# Android
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Docker
export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin/"

# Homebrew
export PATH=/opt/homebrew/bin:$PATH

# Export React Editor
export REACT_EDITOR=code

# 1Password SSH Agent
export SSH_AUTH_SOCK=~/Library/Group\ Containers/2BUA8C4S2C.com.1password/t/agent.sock

# Secrets sourced from 1Password
# YADM_CLASS=$(yadm config local.class)
# if [ "$YADM_CLASS" = "work" ]; then
#    eval "$(op signin --account github)"
#    export GITHUB_TOKEN=$(op item get GITHUB_TOKEN --fields credential)
#    export AZURE_DEVOPS_ACCESS_TOKEN=$(op item get AZURE_DEVOPS_ACCESS_TOKEN --fields credential)
# fi
