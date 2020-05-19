# JINA_CLI_BEGIN

## autocomplete
function __fish_jina_needs_command
  set cmd (commandline -opc)
  if [ (count $cmd) -eq 1 -a $cmd[1] = 'jina' ]
    return 0
  end
  return 1
end

function __fish_jina_using_command
  set cmd (commandline -opc)
  if [ (count $cmd) -gt 1 ]
    if [ $argv[1] = $cmd[2] ]
      return 0
    end
  end
  return 1
end

complete -f -c jina -n '__fish_jina_needs_command' -a '(jina commands)'
for cmd in (jina commands)
  complete -f -c jina -n "__fish_jina_using_command $cmd" -a \
    "(jina completions (commandline -opc)[2..-1])"
end

# session-wise fix
ulimit -n 4096
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# JINA_CLI_END