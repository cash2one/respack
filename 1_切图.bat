@echo off
if "%1" == "" goto noparams
set param1=%1
if %param1:~0,2% == \\ reg add  "HKEY_CURRENT_USER\Software\Microsoft\Command Processor" /v DisableUNCCheck /t REG_DWORD /d 1 /f
cd /d %~dp0 
@cutter.py %1
goto end
:noparams
set SRCPATH=\\192.168.0.2\share\傲视苍穹美术资源
set /p SRCPATH=请输入源图所在目录(默认:%SRCPATH%)
@echo 请选择切图类型：
@echo 1.npc
@echo 2.场景
@echo 3.魔法
@echo 4.武器
@echo 5.角色
@echo 6.ui
@echo 7.timap_mmap
@echo 8.全部
@echo 0.转人工服务
choice /c 123456780
if %ERRORLEVEL% EQU 1 set RESTYPE=npc
if %ERRORLEVEL% EQU 2 set RESTYPE=场景
if %ERRORLEVEL% EQU 3 set RESTYPE=魔法
if %ERRORLEVEL% EQU 4 set RESTYPE=武器
if %ERRORLEVEL% EQU 5 set RESTYPE=角色
if %ERRORLEVEL% EQU 6 set RESTYPE=ui
if %ERRORLEVEL% EQU 7 set RESTYPE=timap_mmap
if %ERRORLEVEL% EQU 8 goto all
if %ERRORLEVEL% EQU 9 goto end
@cutter.py %SRCPATH%\%RESTYPE%
goto end
:all
@cutter.py %SRCPATH%\npc
@cutter.py %SRCPATH%\场景
@cutter.py %SRCPATH%\魔法
@cutter.py %SRCPATH%\武器
@cutter.py %SRCPATH%\角色
:end
pause