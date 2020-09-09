---
title: Using Git Rebase on feature branches
permalink: /editor/git-pull-rebase
layout: default
---

# Feature branches and pull requests

We often work with feature branches which are merged via the GitHub online pull request system. You create new feature branches from an updated dev branch by `git checkout -b feature-whatever`. Once you have committed something, you can push it with `git push origin -u feature-whatever` where the `-u` instructs git to associate your local branch with the new remote branch at origin.
You can then create a pull request in the GitHub UI and merge it there after review.

# Keeping feature branches updated

However in order to keep them up to date we periodically have to update the branches
from the main dev branch. For the most part we prefer it if the branch can be fast-forwarded (put directly on top of the dev-branch with no merging). This means that the rebasing
and possible conflict resolution is handled locally by the developer.

This is where git rebase comes in. If your dev-branch is up to date (you have just run a `git pull --rebase` on it) you can rebase your feature branch by using `git rebase dev` when on your branch. Otherwise you may have to use `git rebase origin/dev` although this may require a `git fetch` first.
The rebase may lead to conflicts which you'll have to resolve locally in the way you typically handle this.
The rebase procedure *will*, however, make a regular push to your feature branch illegal, since it can no longer be fast-forwarded onto your feature-branch.

# git force push

In order to be able to push your updated feature branch to GitHub you have to use force push. The simplest and safest syntax for this is `git push origin +feature-whatever` where the '+' indicates a force of that particular branch. The reason for using this syntax, rather than for instance `git push --force` is that the latter may push several branches and not just *that* particular feature branch.

