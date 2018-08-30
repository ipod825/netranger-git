netranger-git
=============
[vim-netranger](https://github.com/ipod825/vim-netranger) plugin integrating with git.

![Screenshot]()

## Installation
------------

Using vim-plug

```viml
Plug 'ipod825/vim-netranger'
Plug 'ipod825/netranger-git'
```

## Requirements

1. `vim` & `neovim`
    - `echo has('python3')` should output 1

## Usage

### Indicator
1. The following are the meaning of the symbols:
```
[]: The file is unmodified (no change since last commit. Actually, there's no bracket shown).
[M]: The file in theworktree is modified (dirty).
[S]: The modification of the file is staged.
[SM]: Part of the modification of the file is staged, while some other modification is not staged yet.
[U]: The file is not tracked.
[I]: The file is ignored (if it is also ignored by netranger, it will not show up anyway).
```
2. Any operation done by `netranger-git` will automatically update symbols. However, if the states is changed elsewhere, the states might be outdated. In such cases, you could press `r` to refresh the states (`r` is the `vim-netrager` default mapping for refreshing the buffer).

### State Change (stage/unmodify)
1. The following are possible state changes. The middle state represents the current state (please refer to the above description). After pressing `-`/`=`, the file's state becomes the left/right state. `N/A` means there's no sensible state.
```
N/A <- [U] -> [S]
[M] <- [SM] -> [S]
[M] <- [S] -> [S]
[] <- [M] -> [S]  # Note that the left path discard unsaved changes, a warning message will pop up.
[I] <- [I] -> [S]
```

### Interactive Staging (git add --interactive)
1. Press `ed` when cursor is on the file. A diffsplit shows up. On the left hand is the worktree version and on the right is the stage version. On the left hand split, pressing (in visual and normal mode) `=` does a `diffput` and pressing `-` does a `diffget`. On the right hand split, pressing `-` does a `diffput` and pressing `=` does a `diffget`. In short, pressing `=` modifies right hand side and pressing `-` modifies left hand side.
2. On window close of the stage version, its content will be write into the git stage.

## Commit
1. Press `cc`. Edit the commit message. On window close, a git commit is made.
2. Press `ca`. Use the last commit message to make a git commit.
