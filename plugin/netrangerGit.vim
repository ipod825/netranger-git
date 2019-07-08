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


python3 from netranger import api
python3 from netrangerGit.netrangerGit import NETRGit
python3 from netranger.api import NETRApi
python3 netrGit = NETRGit(NETRApi)
python3 NETRApi.RegisterHooker(netrGit.node_highlight_content_l)
python3 NETRApi.RegisterHooker(netrGit.render_begin)
python3 NETRApi.RegisterHooker(netrGit.render_end)
python3 NETRApi.map("cc", netrGit.commit, check=True)
python3 NETRApi.map("ca", netrGit.commit_amend, check=True)
python3 NETRApi.map("ed", netrGit.ediff, check=True)
python3 NETRApi.map("=", netrGit.to_next_state, check=True)
python3 NETRApi.map("-", netrGit.to_prev_state, check=True)

func! _NETRGitDiffStage()
    exec s:pyx 'netrGit.diff_stage()'
endfunc

let &cpo = s:save_cpo
