import contextlib
import os
import sys
import webbrowser
from io import StringIO
from pathlib import Path

import dotenv
from git import Repo, GitCommandError
from github import Github
from invoke import task
from loguru import logger

dotenv.load_dotenv()

GH_COMPAS_DEV = "https://github.com/compas-dev"
GH_BRG_PREFIX = "https://github.com/BlockResearchGroup"

COMPAS_MODULES = {
    "compas": f"{GH_COMPAS_DEV}/compas",
    "compas_fea": f"{GH_COMPAS_DEV}/compas_fea",
    "compas_viewers": f"{GH_COMPAS_DEV}/compas_viewers",
    "compas_fab": f"{GH_COMPAS_DEV}/compas_fab",
    "compas_assembly": f"{GH_BRG_PREFIX}/compas_assembly",
    "compas_triangle": f"{GH_BRG_PREFIX}/compas_triangle",
    "compas_libigl": f"{GH_BRG_PREFIX}/compas_libigl",
    "compas_tna": f"{GH_BRG_PREFIX}/compas_tna",
    "compas_pattern": f"{GH_BRG_PREFIX}/compas_pattern",
    "compas_rbe": f"{GH_BRG_PREFIX}/compas_rbe",
    "compas_ags": f"{GH_BRG_PREFIX}/compas_ags",
    "compas_ghc": f"{GH_BRG_PREFIX}/compas_ghc",
    "compas_3gs": f"{GH_BRG_PREFIX}/compas_3gs",
    "compas_loadpath": f"{GH_BRG_PREFIX}/compas_loadpath",
    "compas_fofin": f"{GH_BRG_PREFIX}/compas_fofin",
}

base_dir = Path(__file__).parent.resolve()


@task(default=True)
def help(ctx):
    """Lists available tasks and usage."""
    ctx.run("invoke --list")
    # log.write('Use "invoke -h <taskname>" to get detailed help for a task.')


def confirm(question):
    while True:
        response = input(question).lower().strip()

        if not response or response in ("n", "no"):
            return False

        if response in ("y", "yes"):
            return True

        print("Focus, kid! It is either (y)es or (n)o", file=sys.stderr)


@contextlib.contextmanager
def chdir(dirname=None):
    current_dir = os.getcwd()
    try:
        if dirname is not None:
            os.chdir(dirname)
        yield
    finally:
        os.chdir(current_dir)


@task()
def conda_install(ctx):
    io = StringIO()
    envs = ctx.run("conda info --envs", out_stream=io)
    io.seek(0)
    out = io.read()

    compas_found = False
    for i in out.splitlines():
        i_strip = i.strip()
        if i_strip.startswith("compas"):
            split_ = i_strip.split()[1]
            logger.debug(f"compas found here: \n\t{split_}\n")
            compas_found = True
            break
    if not compas_found:
        ctx.run("conda env create -c conda-forge --file environment.yml")
    else:
        ctx.run("conda env update -c conda-forge --file environment.yml")


@task()
def pip_install(ctx):
    x = loop_compas_modules()
    repo_dir_ = next(x)

    logger.debug("which pip will be used?")
    ctx.run("which pip")
    ctx.run("pip install -r requirements.txt")

    for k, v, check_mod, check_mod_exists in x:
        logger.info(f"folder: {repo_dir_}")
        if check_mod_exists:
            with chdir(check_mod):
                try:
                    logger.info(f"running pip install for module {v}")
                    ctx.run("pip install -e .")
                except:
                    logger.critical(f"pip install FAILED for module {v}")
                else:
                    logger.info(f"running pip install succeeded")


def loop_compas_modules():
    repo_dir_ = base_dir.parent
    yield repo_dir_
    logger.info(base_dir)

    for k, v in COMPAS_MODULES.items():
        check_mod = repo_dir_ / k
        check_mod_exists = check_mod.exists()
        yield k, v, check_mod, check_mod_exists


@task
def update_modules(ctx, pull=True, fork=False):
    # def update_modules(pull=True, fork=False):
    """Lists available tasks and usage."""

    x = loop_compas_modules()
    repo_dir_ = next(x)

    for k, v, check_mod, check_mod_exists in x:
        logger.info(f"folder: {repo_dir_}")
        logger.info(f"{k}: {v}")
        logger.info(f"module {k} found")

        if check_mod_exists:
            with chdir(check_mod):
                if pull:
                    logger.info(f"updating git repo {k}")
                    ctx.run("git pull")
                    logger.info(f"update complete")
        else:
            # TODO: fork the repo rather than just cloning it
            if not fork:
                ctx.run(f"git clone {v}")
            else:

                # adapted from: https://gist.github.com/christ66/git-fork-clone-upstream.py
                token = os.getenv("GITHUB_TOKEN")

                if token == "NO_TOKEN":
                    logger.info("go fetch me a github token")
                    webbrowser.open("https://github.com/settings/tokens")
                    sys.exit()

                g = Github(token)
                user = g.get_user()
                url = str(v).replace("https://github.com/", "").split("/")
                org = g.get_organization(url[0])

                repo = org.get_repo(url[1])

                my_fork = user.create_fork(repo)

                logger.debug(f"forked repo {url[0]}/{url[1]}")

                try:
                    local_repo = Repo.clone_from(
                        "git@github.com:"
                        + str(user.login)
                        + "/"
                        + str(repo.name)
                        + ".git",
                        base_dir.parent / repo.name,
                        branch="master",
                    )

                    # test if the remote repo doesn't already exist

                    Repo.create_remote(
                        local_repo,
                        "upstream",
                        "git@github.com:" + url[0] + "/" + url[1] + ".git",
                    )
                except GitCommandError:
                    logger.debug(
                        "Directory already exists and is not empty. Not cloning."
                    )
                    pass

                # allow to sync fork with original repo
                # $ git remote add upstream https://github.com/octocat/Spoon-Knife.git


if __name__ == "__main__":
    update_modules(fork=True)
