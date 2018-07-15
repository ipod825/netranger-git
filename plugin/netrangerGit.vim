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

let s:pyx = 'python3 '
exec s:pyx 'from netranger.api import RegisterHooker'
exec s:pyx 'from netranger.api import NETRApi'
exec s:pyx 'from netrangerGit.netrangerGit import NETRGit'
exec s:pyx 'netrGit = NETRGit(NETRApi)'
exec s:pyx 'RegisterHooker(netrGit.node_highlight_content_l)'
exec s:pyx 'RegisterHooker(netrGit.render_begin)'
exec s:pyx 'RegisterHooker(netrGit.render_end)'


let &cpo = s:save_cpo
