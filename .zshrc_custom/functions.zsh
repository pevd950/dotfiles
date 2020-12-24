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