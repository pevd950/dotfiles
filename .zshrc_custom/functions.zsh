# Xcode
openx(){
  if test -n "$(find . -maxdepth 1 -name '*.xcworkspace' -print -quit)"
  then
	echo "Opening workspace"
	open *.xcworkspace
	return
  else
	if test -n "$(find . -maxdepth 1 -name '*.xcodeproj' -print -quit)"
	then
	  echo "Opening project"
	  open *.xcodeproj
	  return
	else
	  echo "Nothing found"
	fi
  fi
}

# turn hidden files on/off in Finder
function hiddenOn() { defaults write com.apple.Finder AppleShowAllFiles YES ; }
function hiddenOff() { defaults write com.apple.Finder AppleShowAllFiles NO ; }

# myIP address
function myip() {
    ifconfig lo0 | grep 'inet ' | sed -e 's/:/ /' | awk '{print "lo0       : " $2}'
	ifconfig en0 | grep 'inet ' | sed -e 's/:/ /' | awk '{print "en0 (IPv4): " $2 " " $3 " " $4 " " $5 " " $6}'
	ifconfig en0 | grep 'inet6 ' | sed -e 's/ / /' | awk '{print "en0 (IPv6): " $2 " " $3 " " $4 " " $5 " " $6}'
	ifconfig en1 | grep 'inet ' | sed -e 's/:/ /' | awk '{print "en1 (IPv4): " $2 " " $3 " " $4 " " $5 " " $6}'
	ifconfig en1 | grep 'inet6 ' | sed -e 's/ / /' | awk '{print "en1 (IPv6): " $2 " " $3 " " $4 " " $5 " " $6}'
}

# Show file in quick look
function quick-look() {
  (( $# > 0 )) && qlmanage -p $* &>/dev/null &
}

# Open man page in preview app
preman() {
    mandoc -T pdf "$(/usr/bin/man -w $@)" | open -fa Preview
}
# Expose kubernetes context for iTerm
iterm2_print_user_vars() {
	KUBECONTEXT=$(CTX=$(kubectl config current-context) 2> /dev/null;if [ $? -eq 0 ]; then echo $CTX;fi)
	iterm2_set_user_var kubeContext $KUBECONTEXT
}

copilot_gh-assist() {
        TMPFILE=$(mktemp)
        trap 'rm -f $TMPFILE' EXIT
        if /Users/pvd950/.nvm/versions/node/v16.15.1/bin/github-copilot-cli gh-assist "$@" --shellout $TMPFILE; then
                if [ -e "$TMPFILE" ]; then
                        FIXED_CMD=$(cat $TMPFILE)
                        print -s "$FIXED_CMD"
                        eval "$FIXED_CMD"
                else
                        echo "Apologies! Extracting command failed"
                fi
        else
                return 1
        fi
}

copilot_git-assist() {
        TMPFILE=$(mktemp)
        trap 'rm -f $TMPFILE' EXIT
        if /Users/pvd950/.nvm/versions/node/v16.15.1/bin/github-copilot-cli git-assist "$@" --shellout $TMPFILE; then
                if [ -e "$TMPFILE" ]; then
                        FIXED_CMD=$(cat $TMPFILE)
                        print -s "$FIXED_CMD"
                        eval "$FIXED_CMD"
                else
                        echo "Apologies! Extracting command failed"
                fi
        else
                return 1
        fi
}

copilot_what-the-shell() {
        TMPFILE=$(mktemp)
        trap 'rm -f $TMPFILE' EXIT
        if /Users/pvd950/.nvm/versions/node/v16.15.1/bin/github-copilot-cli what-the-shell "$@" --shellout $TMPFILE; then
                if [ -e "$TMPFILE" ]; then
                        FIXED_CMD=$(cat $TMPFILE)
                        print -s "$FIXED_CMD"
                        eval "$FIXED_CMD"
                else
                        echo "Apologies! Extracting command failed"
                fi
        else
                return 1
        fi
}
