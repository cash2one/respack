@echo off
@if "%1" == "" goto noparams
@exporter.py %1
@goto end
:noparams
set RESZIP=res.zip
set /p RESZIP=请输入资源文件名(默认:%RESZIP%)
@exporter.py %RESZIP%
:end