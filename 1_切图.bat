@echo off
@if "%1" == "" goto noparams
@cutter.py %1
@goto end
:noparams
@echo 请选择切图类型：
@echo 1.npc
@echo 2.场景
@echo 3.魔法
@echo 4.武器
@echo 5.角色
@echo 6.全部
@echo 0.转人工服务
choice /c 1234560
if %ERRORLEVEL% EQU 1 set RESTYPE=npc
if %ERRORLEVEL% EQU 2 set RESTYPE=场景
if %ERRORLEVEL% EQU 3 set RESTYPE=魔法
if %ERRORLEVEL% EQU 4 set RESTYPE=武器
if %ERRORLEVEL% EQU 5 set RESTYPE=角色
if %ERRORLEVEL% EQU 6 goto all
if %ERRORLEVEL% EQU 7 goto end
@cutter.py %RESTYPE%
goto end
:all
@cutter.py npc
@cutter.py 场景
@cutter.py 魔法
@cutter.py 武器
@cutter.py 角色
:end