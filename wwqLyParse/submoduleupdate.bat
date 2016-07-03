@rem git submodule foreach git pull
cd ykdl
git pull https://github.com/zhangn1985/ykdl.git master
git push --force
cd..
cd you-get
git pull https://github.com/soimort/you-get.git master
git push --force
cd..
cd p_video
git pull https://github.com/sceext2/p_video.git pv-8
git push --force
@pause