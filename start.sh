#!/usr/bin/env bash
apache2ctl start
${WORK_DIR}/gitRepoMonitor.py > ${LOG_DIR}/program_log.log 2>&1
