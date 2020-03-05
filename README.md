# 0. Preparation
1. Make Auth.json in directory  
You can get git auth token from github : Settings / Developer settings / Personal access tokens  
```
Example)

{
    "USER":"wnaldj1589TW",
    "AUTH":"1234576879080abcdefghijklmnopqr"
}
```

2. Make ssh key  
Use `ssh-keygen`.  

3. Choose target repositories  
If you set the value of `GIT_TARGET` in Dockerfile, you can choose the target repositories.  
If you set `GIT_TARGET` as `twinnylab`, python script will collect repositories that only contains given `GIT_TARGET` in url.  

4. Check available ports  
In this README.md, docker container will use 9999 port as default port.  
Please check 9999 port of your system.  

# 1. Execution
docker build --tag doxygen_monitor:0.1 --build-arg ssh_pub_key="$(cat ~/.ssh/id_rsa.pub)" --build-arg ssh_prv_key="$(cat ~/.ssh/id_rsa)" .  
docker run -d -p9999:8888 --name doxygen -v /work/log:./work doxygen_monitor:0.1 ./start.sh

# 2. Caution
1. If there is no ProjectInfo.h in include directories in your repository, docker container won't show that repository.  
2. Log for the script will be created in log directory.

# 3. TO DO
1. Update frontend.  
2. Speed up monitoring interval if it is available  
