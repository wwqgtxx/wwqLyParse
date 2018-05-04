@rem git submodule foreach git pull
cd %~dp0/ykdl
git pull https://github.com/zhangn1985/ykdl.git master
git push --force
cd %~dp0/you-get
git pull https://github.com/soimort/you-get.git develop
git push --force
cd %~dp0/annie/src/github.com/iawia002/annie
git pull https://github.com/iawia002/annie.git master
git push --force
cd %~dp0
@pause