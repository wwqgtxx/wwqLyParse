@rem git submodule foreach git pull
cd ykdl
git pull --rebase https://github.com/zhangn1985/ykdl.git master
git push --force
cd..
cd you-get
git pull --rebase https://github.com/soimort/you-get.git master
git push --force
cd..
cd p_video
git pull --rebase https://github.com/sceext2/p_video/tree/pv-8.git master
git push --force
@pause