@echo off
@if "%1" == "" goto noparams
@exporter.py %1
@goto end
:noparams
set RESZIP=res.zip
set /p RESZIP=��������Դ�ļ���(Ĭ��:%RESZIP%)
@exporter.py %RESZIP%
:end