#!/usr/bin/env python3
import json
import requests
import base64
import pprint
import os, glob, pathlib
import time
import git

USER = ''
API_TOKEN = ''
GIT_API_URL = 'https://api.github.com'
WWW_DIR = os.environ["WWW_DIR"]
WORK_DIR = os.environ["WORK_DIR"]
REPO_DIR = WORK_DIR+"/repos"
LOG_DIR = os.environ["LOG_DIR"]
GIT_TARGET = os.environ["GIT_TARGET"]
GIT_REPOS = {}

def readAuth(fname):
    global USER, API_TOKEN
    try:
        j = json.load(open(fname))
        USER = j["USER"]
        API_TOKEN = j["AUTH"]
    except FileNotFoundError:
        LOG_MSG("[Error] given path is not valid. please set path correctly")
    except json.decoder.JSONDecodeError:
        LOG_MSG("[Error] format of given auth json file is not proper.")
        LOG_MSG("[Error] file should be set like {\"USER\":\"USER_NAME\", \"AUTH\":\"TOKEN\"}")
    except:
        raise

def downloadRepo(url):
    global USER, API_TOKEN, GIT_REPOS
    b = '{:s}/token:{:s}'.format(USER, API_TOKEN)
    b = b.encode("UTF-8")
    base64string = base64.b64encode(b).decode("UTF-8")
    headers = {"Authorization": "Basic {:s}".format(base64string), "Accept":"application/vnd.github.machine-man-preview+json"}
    response = requests.get(GIT_API_URL + url, headers=headers)
    for git in response.json():
        git_url = git["ssh_url"]
        if GIT_TARGET in git_url \
                and git["archived"] == False \
                and git["disabled"] == False \
                and git_url not in GIT_REPOS:
            LOG_MSG(git_url)
            GIT_REPOS[git_url] = 1
            os.chdir(REPO_DIR)
            os.system("git clone {:s}".format(git_url))
            LOG_MSG("git clone {:s}".format(git_url))

def updateRepo():
    global WORK_DIR, REPO_DIR

    repos = glob.glob(REPO_DIR+"/*")
    for repo in repos:
        g = git.cmd.Git(repo)
        try:
            g.checkout("devel")
            g.checkout("develop")
        except:
            pass
        try:
            g.pull()
        except:
            LOG_MSG("[Error] {:s}".format(repo))
        os.chdir(repo)
        if isProjectInfoContained(repo):
            os.system("doxygen {:s}/Doxyfile > /dev/null".format(WORK_DIR))
            LOG_MSG("doxygen {:s}/Doxyfile > /dev/null".format(WORK_DIR))

def copyDoxygen():
    global WORK_DIR, REPO_DIR
    repos = glob.glob(REPO_DIR+"/*")
    for repo in repos:
        packageName = repo.split("/")[-1]
        if isProjectInfoContained(repo) == True:
            try:
                os.mkdir("{:s}/{:s}".format(WWW_DIR, packageName))
            except FileExistsError:
                LOG_MSG("mkdir failed, {:s}/{:s}".format(WWW_DIR, packageName))
                pass
            try:
                os.chdir(repo)
            except FileNotFoundError:
                LOG_MSG("chdir failed, {:s} not found".format(repo))
                pass
            os.system("cp -r {:s}/html/* {:s}/{:s}".format(repo, WWW_DIR, packageName))
            LOG_MSG("cp -r {:s}/html/* {:s}/{:s}".format(repo, WWW_DIR, packageName))

def isProjectInfoContained(repo):
    find = False
    p = pathlib.Path("{:s}/include".format(repo))
    for f in p.glob("**/*"):
        if f.name == "ProjectInfo.h":
            find = True
            break
    return find

def LOG_MSG(msg):
    LOG_FILE.write(msg+"\n")


if __name__ == "__main__":
    readAuth("Auth.json")
    LOG_FILE = open("{:s}/{:s}.LOG_MSG".format(LOG_DIR, str(time.time())), "w")
    while True:
        for i in range(10):
            downloadRepo("/user/repos?page={:d}&per_page=100".format(i))
        updateRepo()
        copyDoxygen()
        time.sleep(3600)
    LOG_FILE.close()
