if !exists("g:loaded_netranger")
    echoerr "netranger must be initialized before plugin initialized"
    finish
endif
if exists("g:loaded_netranger_diricon") || &cp
    finish
endif
let g:loaded_netranger_diricon = 1

let s:save_cpo = &cpo
set cpo&vim

if !has('python3') && !has('python')
    echo "Error: Required vim compiled with +python or +python3"
    finish
endif


if has('python3')
    let s:pyx = 'python3 '
else
    let s:pyx = 'python '
endif

exec s:pyx 'from netranger import api'
exec s:pyx 'from netrangerGit.netrangerGit import NETRGit'
exec s:pyx 'netrGit = NETRGit(api.NETRApi)'
exec s:pyx 'api.RegisterHooker(netrGit.node_highlight_content_l)'
exec s:pyx 'api.RegisterHooker(netrGit.render_begin)'
exec s:pyx 'api.RegisterHooker(netrGit.render_end)'
exec s:pyx 'api.RegisterKeyMaps([
            \ ("cc", netrGit.commit),
            \ ("ca", netrGit.commit_amend),
            \ ("ed", netrGit.ediff),
            \ ("=", netrGit.to_next_state),
            \ ("-", netrGit.to_prev_state),
            \ ])'

func! _NETRGitDiffStage()
    exec s:pyx 'netrGit.diff_stage()'
endfunc

let &cpo = s:save_cpo
