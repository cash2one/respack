@echo off
@if "%1" == "" goto noparams
@cutter.py %1
@goto end
:noparams
@echo ��ѡ����ͼ���ͣ�
@echo 1.npc
@echo 2.����
@echo 3.ħ��
@echo 4.����
@echo 5.��ɫ
@echo 6.ȫ��
@echo 0.ת�˹�����
choice /c 1234560
if %ERRORLEVEL% EQU 1 set RESTYPE=npc
if %ERRORLEVEL% EQU 2 set RESTYPE=����
if %ERRORLEVEL% EQU 3 set RESTYPE=ħ��
if %ERRORLEVEL% EQU 4 set RESTYPE=����
if %ERRORLEVEL% EQU 5 set RESTYPE=��ɫ
if %ERRORLEVEL% EQU 6 goto all
if %ERRORLEVEL% EQU 7 goto end
@cutter.py %RESTYPE%
goto end
:all
@cutter.py npc
@cutter.py ����
@cutter.py ħ��
@cutter.py ����
@cutter.py ��ɫ
:end