import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'GitPython'))
from git import Repo
from git import InvalidGitRepositoryError, GitCommandError


class RepoWrapper(object):
    def __init__(self, path):
        self.repo = Repo(path)
        self.path = path
        self.path_len = len(path) + 1

    def relative_path(self, path):
        return path[self.path_len:]

    def is_untracked(self, path):
        return path in self.repo.untracked_files

    def is_staged(self, path):
        return len(self.repo.index.diff('HEAD', paths=path))>0

    def is_modified(self, path):
        return len(self.repo.index.diff(None, paths=path))>0

    def is_ignored(self, path):
        try:
            self.repo.git.execute(['git', 'check-ignore', path])
        except GitCommandError:
            return False
        return True


class NETRGit(object):
    def __init__(self, api):
        self.api = api
        self.cur_repo = None
        self.nodes_to_handle_count = 0
        self.repo_cache = {}
        self.icon_map = {
            "Modified": ('[M]', 1),
            "Staged": ('[S]', 2),
            "StagedModified": ('[SM]', 1),
            "Untracked": ('[U]', 5),
            "Unmerged": ('[═]', 1),
            "Dirty": ('[✗]', 1),
            'Ignored': ('[I]', 0),
        }
        self.call_by_render = False

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

    def node_highlight_content_l(self, node):
        if self.call_by_render:
            if self.nodes_to_handle_count > 0:
                self.nodes_to_handle_count -= 1
                return self.get_status(node)
            elif node.isDir and node.expanded:
                # Check if the current node is a directory of a git repo
                # If so, we need to set highlight content for all following nodes
                # with level greater than that of the current node
                if self.set_cur_repo(node.fullpath):
                    nodeInd = self.api.node_index(node)
                    self.nodes_to_handle_count = self.api.next_lesseq_level_ind(nodeInd) - nodeInd - 1

                    print(node.fullpath, self.get_status(node))
                    return self.get_status(node)
        else:
            if self.set_cur_repo(os.path.dirname(node.fullpath)):
                return self.get_status(node)
        return '', 0

    def all_parent_path(self, path):
        while len(path)>1:
            yield path
            path = os.path.dirname(path)

    def set_cur_repo(self, path):
        for p in self.all_parent_path(path):
            if p in self.repo_cache:
                self.cur_repo = self.repo_cache[p]
                return True
            try:
                self.cur_repo = RepoWrapper(p)
            except InvalidGitRepositoryError:
                continue
            self.repo_cache[p] = self.cur_repo
            return True
        return False

    def get_status(self, node):
        path = self.cur_repo.relative_path(node.fullpath)
        if len(path) == 0:
            return '', 0
        if self.cur_repo.is_untracked(path):
            return self.icon_map['Untracked']
        elif self.cur_repo.is_staged(path):
            if self.cur_repo.is_modified(path):
                return self.icon_map['StagedModified']
            return self.icon_map['Staged']
        elif self.cur_repo.is_modified(path):
            return self.icon_map['Modified']
        elif self.cur_repo.is_ignored(path):
            return self.icon_map['Ignored']
        return '', 0
