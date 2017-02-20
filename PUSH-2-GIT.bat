@echo off

REM prompt $G

cls

mysqldump -uroot -proot --add-drop-database  jd > jd.sql

set d=%date%

REM set d=%d:~3,13%
set d=%d:~0,10%

set d=%d:/=-%

set t=%time:~0,8%

set dt=%d% %t%

echo %dt%

git add .

git commit -m "%dt%"

git push

REM echo "push over..."

REM pause