#!/bin/sh

echo "gitlabSourceRepoURL=$CI_REPOSITORY_URL
gitlabCommitSha=$CI_COMMIT_SHA
gitlabShortCommit=$(git rev-parse --short ${CI_COMMIT_SHA:-HEAD})
gitlabAfter=abcdefghijklmnopqrstuvwxyz0123456789abcd
gitlabTargetBranch=master
gitlabSourceRepoHttpUrl=https://gitlab.eng.asnyder.com/cloudtech/cti-slackbud.git
gitlabMergeRequestLastCommit=abcdefghijklmnopqrstuvwxyz0123456789abcd
gitlabSourceRepoSshUrl=git@gitlab.eng.asnyder.com:cloudtech/cti-slackbud.git
gitlabSourceRepoHomepage=https://gitlab.eng.asnyder.com/cloudtech/cti-slackbud
gitlabBranch=$CI_COMMIT_REF_SLUG
gitlabSourceBranch=master
gitlabUserEmail=$GITLAB_USER_EMAIL
gitlabBefore=abcdefghijklmnopqrstuvwxyz0123456789abcd
gitlabActionType=PUSH
gitlabSourceRepoName=cti-slackbud
gitlabSourceNamespace=cloudtech
gitlabUserName=$GITLAB_USER_NAME
BUILD_NUMBER=$CI_PIPELINE_ID
" > githook_info.txt

