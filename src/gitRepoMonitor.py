#!/usr/bin/env python3
import json
import requests
import base64
import pprint
import os, glob, pathlib
import time
import git
import threading

USER = ''
API_TOKEN = ''
GIT_API_URL = 'https://api.github.com'
WWW_DIR = os.environ["WWW_DIR"]
WORK_DIR = os.environ["WORK_DIR"]
REPO_DIR = WORK_DIR+"/repos"
LOG_DIR = os.environ["LOG_DIR"]
GIT_TARGET = os.environ["GIT_TARGET"]

START_TIME = time.time()
MONITORING_INTERVAL = 600

REPO_DOWNLOADED = 0
REPO_UPDATED = 1
DOXYGEN_UPDATED = 2

def readAuth(fname):
    global USER, API_TOKEN
    try:
        j = json.load(open(fname))
        USER = j["USER"]
        API_TOKEN = j["AUTH"]
    except FileNotFoundError:
        ERROR_MSG("[Error] given path is not valid. please set path correctly")
    except json.decoder.JSONDecodeError:
        ERROR_MSG("[Error] format of given auth json file : {:s} is not proper".format(fname))
        ERROR_MSG("[Error] file should be set like {\"USER\":\"USER_NAME\", \"AUTH\":\"TOKEN\"}")
    except Exception as e:
        ERROR_MSG("[Error] {:s} ".format(repo) + str(e))
        raise

def getLockedList():
    locked_list = {}
    try:
        with open(REPO_DIR + "/.repo-lock", "r") as locked_list_file:
            locked_list = json.load(locked_list_file)
    except:
        pass
    return locked_list

def updateLockedList(locked_list):
    with open(REPO_DIR + "/.repo-lock", "w") as locked_list_file:
        json.dump(locked_list, locked_list_file, indent=4)

def flushLockedList():
    try:
        os.remove(REPO_DIR + "/.repo-lock")
    except:
        pass


def downloadRepo(url, locked_list):
    global USER, API_TOKEN
    b = '{:s}/token:{:s}'.format(USER, API_TOKEN)
    b = b.encode("UTF-8")
    base64string = base64.b64encode(b).decode("UTF-8")
    headers = {"Authorization": "Basic {:s}".format(base64string), "Accept":"application/vnd.github.machine-man-preview+json"}
    response = requests.get(GIT_API_URL + url, headers=headers)
    for git in response.json():
        git_url = git["ssh_url"]
        if GIT_TARGET in git_url \
                and git["archived"] == False \
                and git["disabled"] == False:
            repo_name = git_url.split("/")[-1]
            if repo_name in locked_list \
                    and locked_list[repo_name] >= REPO_DOWNLOADED:
                continue
            os.chdir(REPO_DIR)
            git_url = git_url[3:].replace(":", "/")
            git_url = "https://{:s}:{:s}".format(USER, API_TOKEN) + git_url
            os.system("git clone {:s}".format(git_url))
            INFO_MSG("git clone {:s}".format(git_url))
            try:
                locked_list[repo_name] = REPO_DOWNLOADED
                updateLockedList(locked_list)
            except:
                continue

def updateRepo(locked_list):
    global WORK_DIR, REPO_DIR

    def update(repo):
        g = git.cmd.Git(repo)
        try:
            g.checkout("devel")
            g.checkout("develop")
        except Exception as e:
            ERROR_MSG("[Error] {:s} ".format(repo) + str(e))
        try:
            g.pull()
        except Exception as e:
            ERROR_MSG("[Error] {:s} ".format(repo) + str(e))
        if isProjectInfoContained(repo):
            INFO_MSG("Found ProjectInfo.h in {:s}".format(repo))
            if repo in locked_list \
                    and locked_list[repo] >= REPO_UPDATED:
                return
            os.system("cd {:s};doxygen {:s}/Doxyfile".format(repo, WORK_DIR))
            INFO_MSG("doxygen {:s}/Doxyfile in {:s}".format(WORK_DIR, repo))
            locked_list[repo] = REPO_UPDATED
            updateLockedList(locked_list)
        else:
            INFO_MSG("No ProjectInfo.h in {:s}".format(repo))

    repos = glob.glob(REPO_DIR+"/*")
    thread_list = []
    for repo in repos:
        t = threading.Thread(target=update, args=(repo,))
        t.start()
        thread_list.append(t)
    for t in thread_list:
        t.join()

def copyDoxygen(locked_list):
    global WORK_DIR, REPO_DIR
    def copy(repo):
        packageName = repo.split("/")[-1]
        if isProjectInfoContained(repo) == True:
            try:
                os.mkdir("{:s}/{:s}".format(WWW_DIR, packageName))
                INFO_MSG("mkdir {:s}/{:s}".format(WWW_DIR, packageName))
            except FileExistsError as e:
                ERROR_MSG("mkdir failed, {:s}/{:s} ".format(WWW_DIR, packageName) + str(e))
            except Exception as e:
                ERROR_MSG("[Error] {:s} ".format(repo) + str(e))

            os.system("cp -r {:s}/html/* {:s}/{:s}".format(repo, WWW_DIR, packageName))
            INFO_MSG("cp -r {:s}/html/* {:s}/{:s}".format(repo, WWW_DIR, packageName))
            locked_list[repo] = DOXYGEN_UPDATED 
            updateLockedList(locked_list)

    repos = glob.glob(REPO_DIR+"/*")
    for repo in repos:
        t = threading.Thread(target=copy, args=(repo,))
        t.start()
        t.join()

def isProjectInfoContained(repo):
    find = False
    p = pathlib.Path("{:s}/include".format(repo))
    for f in p.glob("**/*"):
        if f.name == "ProjectInfo.h":
            find = True
            break
    return find

def INFO_MSG(msg):
    INFO_LOG = open("{:s}/{:s}.INFO.log".format(LOG_DIR, str(START_TIME)), "a")
    INFO_LOG.write(msg+"\n")
    INFO_LOG.close()

def ERROR_MSG(msg):
    ERROR_LOG = open("{:s}/{:s}.ERROR.log".format(LOG_DIR, str(START_TIME)), "w")
    ERROR_LOG.write(msg+"\n")
    ERROR_LOG.close()


if __name__ == "__main__":
    readAuth("Auth.json")

    if len(GIT_TARGET) == 0:
        ERROR_MSG("[Error] please set GIT_TARGET in Dockerfile")

    while True:
        locked_list = getLockedList()
        for i in range(10):
            downloadRepo("/user/repos?page={:d}&per_page=100".format(i), locked_list)
        updateRepo(locked_list)
        copyDoxygen(locked_list)
        flushLockedList()
        time.sleep(MONITORING_INTERVAL)
