import os
import random
import re
import shutil
import tempfile

import vim
from netranger import Vim
from netranger.enum import Enum
from netranger.shell import Shell


class Repo(object):
    State = Enum(
        'GitState',
        'INVALID, IGNORED, UNTRACKED, UNMODIFIED, MODIFIED, STAGED, '
        'STAGEDMODIFIED, UNMERGED')

    def __init__(self, path):
        self.path = path
        self.path_len = len(path) + 1

        self.staged_str = None
        self.modified_str = None
        self.ignored_str = None
        self.commit_edit_msg = os.path.join(self.path, '.git/COMMIT_EDITMSG')

    def run_cmd(self, cmd):
        return Shell.run('git -C {} {}'.format(self.path, cmd))

    def get_state(self, fullpath):
        rel_path = fullpath[self.path_len:]
        if os.path.isdir(fullpath):
            if not rel_path:
                return Repo.State.INVALID
            if self.staged_str is None:
                self.staged_str = self.run_cmd('diff --name-only --cached')
                self.modified_str = self.run_cmd('ls-files -m')
                self.ignored_str = self.run_cmd(
                    'ls-files --others -i --exclude-standard')
            if re.search(rel_path, self.staged_str):
                if re.search(rel_path, self.modified_str):
                    return Repo.State.STAGEDMODIFIED
                else:
                    return Repo.State.STAGED
            elif re.search(rel_path, self.modified_str):
                return Repo.State.MODIFIED
            elif re.search(rel_path + '\n', self.ignored_str):
                return Repo.State.IGNORED
            else:
                return Repo.State.INVALID
        else:
            state_str = self.run_cmd(
                'status --porcelain --ignored -uall {}'.format(rel_path))
            if state_str:
                return {
                    "!!": Repo.State.IGNORED,
                    '??': Repo.State.UNTRACKED,
                    ' M': Repo.State.MODIFIED,
                    'MM': Repo.State.STAGEDMODIFIED,
                    'M ': Repo.State.STAGED
                }[state_str[:2]]
            else:
                return Repo.State.INVALID

    def get_prev_and_next_state(self, fullpath):
        cur_state = self.get_state(fullpath)
        if cur_state == Repo.State.UNTRACKED:
            return Repo.State.INVALID, Repo.State.STAGED
        elif (cur_state == Repo.State.STAGEDMODIFIED
              or cur_state == Repo.State.STAGED):
            return Repo.State.MODIFIED, Repo.State.STAGED
        elif cur_state == Repo.State.MODIFIED:
            return Repo.State.UNMODIFIED, Repo.State.STAGED
        elif cur_state == Repo.State.IGNORED:
            return Repo.State.INVALID, Repo.State.STAGED
        elif cur_state == Repo.State.INVALID:
            return Repo.State.INVALID, Repo.State.INVALID
        else:
            assert False, "get_prev_and_next_state: "
            "Unhandled case: " + cur_state

    def stage(self, fullpath):
        self.run_cmd('add {}'.format(fullpath))

    def unstage(self, fullpath):
        self.run_cmd('reset HEAD {}'.format(fullpath))

    def unmodify(self, fullpath):

        ans = Vim.UserInput("This will discard any made changes. Proceed "
                            "anyway? (y/n)")
        if ans == 'y':
            self.run_cmd('checkout {}'.format(fullpath))

    def commit(self, amend=False):
        if amend:
            # TODO Should we check if already pushed?
            return self.run_cmd('commit --amend --no-edit')
        else:
            with open(self.commit_edit_msg, 'w') as file:
                lines = []
                for line in file:
                    line = line.strip()
                    if line and line[0] != '#':
                        lines.append(line)
                if len(lines) > 0:
                    return self.run_cmd('commit -m "{}"'.format(
                        ''.join(lines)))

    def stage_file_content(self, fullpath):
        rel_path = fullpath[self.path_len:]
        return self.run_cmd('cat-file -p :{}'.format(rel_path))


class NETRGit(object):
    def __init__(self, api):
        self.api = api
        self.cur_repo = None
        self.nodes_to_handle_count = 0
        self.icon_map = {
            Repo.State.INVALID: ('', 0),
            Repo.State.UNMODIFIED: ('', 0),
            Repo.State.MODIFIED: ('[M]', 1),
            Repo.State.STAGED: ('[S]', 2),
            Repo.State.STAGEDMODIFIED: ('[SM]', 1),
            Repo.State.UNTRACKED: ('[U]', 5),
            Repo.State.UNMERGED: ('[=]', 1),
            Repo.State.IGNORED: ('[I]', 0),
        }
        self.call_by_render = False
        while True:
            self.cache_dir = os.path.join(tempfile.gettempdir(),
                                          str(random.randint(0, 1e10)))
            if os.path.isdir(self.cache_dir):
                continue
            os.makedirs(self.cache_dir)
            os.chmod(self.cache_dir, 0o700)
            break

    def render_begin(self, buf):
        # let node_highlight_content_l know that it is being
        # called by render for more efficient handling.
        self.call_by_render = True

        # Check if current buf is a (sub)directory of a git repo.
        # If so, we need to set highlight content for all nodes,
        # hence set nodes_to_handle_count = # of all nodes
        if self.set_cur_repo(buf.wd):
            self.nodes_to_handle_count = len(buf.nodes)

    def render_end(self, buf):
        self.call_by_render = False

    def get_state_icon(self, fullpath):
        return self.icon_map[self.cur_repo.get_state(fullpath)]

    def node_highlight_content_l(self, node):
        if self.call_by_render:
            if self.nodes_to_handle_count > 0:
                self.nodes_to_handle_count -= 1
                return self.get_state_icon(node.fullpath)
            elif node.is_DIR and node.expanded:
                # Check if the current node is a directory of a git repo
                # If so, we need to set highlight content for all following
                # nodes with level greater than that of the current node
                if self.set_cur_repo(node.fullpath):
                    nodeInd = self.api.node_index(node)
                    self.nodes_to_handle_count = \
                        self.api.next_lesseq_level_ind(nodeInd) - nodeInd - 1

                    return self.get_state_icon(node.fullpath)
        else:
            if self.set_cur_repo(os.path.dirname(node.fullpath)):
                return self.get_state_icon(node.fullpath)
        return self.icon_map[Repo.State.UNMODIFIED]

    def all_parent_path(self, path):
        while len(path) > 1:
            yield path
            path = os.path.dirname(path)

    def set_cur_repo(self, path):
        for p in self.all_parent_path(path):
            if os.path.isdir(os.path.join(p, '.git')):
                self.cur_repo = Repo(p)
                return True
        return False

    def to_next_state(self):
        cur_node = self.api.cur_node()
        if self.set_cur_repo(cur_node.fullpath):
            _, state = self.cur_repo.get_prev_and_next_state(cur_node.fullpath)
            if state == Repo.State.STAGED:
                self.cur_repo.stage(cur_node.fullpath)
            elif state == Repo.State.INVALID:
                return
            else:
                assert False, "next_state: Case not handled!"
            self.api.render()

    def to_prev_state(self):
        cur_node = self.api.cur_node()
        if self.set_cur_repo(cur_node.fullpath):
            state, _ = self.cur_repo.get_prev_and_next_state(cur_node.fullpath)
            if state == Repo.State.MODIFIED:
                self.cur_repo.unstage(cur_node.fullpath)
            elif state == Repo.State.UNMODIFIED:
                self.cur_repo.unmodify(cur_node.fullpath)
            elif state == Repo.State.INVALID:
                return
            else:
                assert False, "prev_state: Case not handled!"

        self.api.render()

    def commit(self):
        bufNum = vim.current.buffer.number
        Shell.run('GIT_EDITOR=false git commit')
        vim.command('tabe {}'.format(self.cur_repo.commit_edit_msg))
        vim.command('setlocal bufhidden=wipe')
        vim.command(
            'autocmd bufunload <buffer> :py3 netrGit.post_commit({})'.format(
                bufNum))

    def commit_amend(self):
        msg = self.cur_repo.commit(amend=True)
        self.api.render()
        Vim.Echo(msg)

    def post_commit(self, bufNum):
        msg = self.cur_repo.commit()
        self.api.render(bufNum)
        Vim.Echo(msg)

    def ediff(self):
        cur_node = self.api.cur_node()
        basename = os.path.basename(cur_node.fullpath)
        if cur_node.is_DIR:
            return
        temp_stage_file = '{}/STAGE:{}'.format(
            os.path.dirname(vim.eval('tempname()')), basename)
        with open(temp_stage_file, 'w') as file:
            file.write(self.cur_repo.stage_file_content(cur_node.fullpath))
        vim.command('tabe {}'.format(temp_stage_file))
        vim.command('setlocal noswapfile')
        vim.command('setlocal bufhidden=wipe')
        # do the map here
        vim.command('nnoremap <buffer> = :diffget<CR>')
        vim.command('vnoremap <buffer> = :diffget<CR>')
        vim.command('nnoremap <buffer> - :diffput<CR>')
        vim.command('vnoremap <buffer> - :diffput<CR>')
        vim.command(
            'autocmd bufunload <buffer> :py3 netrGit.ediff_post("{}","{}")'.
            format(temp_stage_file, cur_node.fullpath))

        vim.command('leftabove diffsplit {}'.format(cur_node.fullpath))
        vim.command('nnoremap <buffer> - :diffget<CR>')
        vim.command('vnoremap <buffer> - :diffget<CR>')
        vim.command('nnoremap <buffer> = :diffput<CR>')
        vim.command('vnoremap <buffer> = :diffput<CR>')

    def ediff_post(self, stage_file, worktree_file):
        tmp_file_name = worktree_file + 'netrangergit_tmp'
        shutil.move(worktree_file, tmp_file_name)
        shutil.move(stage_file, worktree_file)
        self.set_cur_repo(worktree_file)
        self.cur_repo.stage(worktree_file)
        shutil.move(tmp_file_name, worktree_file)
