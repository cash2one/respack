@echo off
if "%1" == "" goto noparams
set param1=%1
if %param1:~0,2% == \\ reg add  "HKEY_CURRENT_USER\Software\Microsoft\Command Processor" /v DisableUNCCheck /t REG_DWORD /d 1 /f
cd /d %~dp0 
@cutter.py %1
goto end
:noparams
set SRCPATH=\\192.168.0.2\share\���Ӳ��������Դ
set /p SRCPATH=������Դͼ����Ŀ¼(Ĭ��:%SRCPATH%)
@echo ��ѡ����ͼ���ͣ�
@echo 1.npc
@echo 2.����
@echo 3.ħ��
@echo 4.����
@echo 5.��ɫ
@echo 6.ui
@echo 7.timap_mmap
@echo 8.ȫ��
@echo 0.ת�˹�����
choice /c 123456780
if %ERRORLEVEL% EQU 1 set RESTYPE=npc
if %ERRORLEVEL% EQU 2 set RESTYPE=����
if %ERRORLEVEL% EQU 3 set RESTYPE=ħ��
if %ERRORLEVEL% EQU 4 set RESTYPE=����
if %ERRORLEVEL% EQU 5 set RESTYPE=��ɫ
if %ERRORLEVEL% EQU 6 set RESTYPE=ui
if %ERRORLEVEL% EQU 7 set RESTYPE=timap_mmap
if %ERRORLEVEL% EQU 8 goto all
if %ERRORLEVEL% EQU 9 goto end
@cutter.py %SRCPATH%\%RESTYPE%
goto end
:all
@cutter.py %SRCPATH%\npc
@cutter.py %SRCPATH%\����
@cutter.py %SRCPATH%\ħ��
@cutter.py %SRCPATH%\����
@cutter.py %SRCPATH%\��ɫ
:end
pause