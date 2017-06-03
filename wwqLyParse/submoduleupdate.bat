@rem git submodule foreach git pull
cd ykdl
git pull https://github.com/zhangn1985/ykdl.git master
git push --force
cd..
cd you-get
git pull https://github.com/soimort/you-get.git develop
git push --force
cd..
@pause