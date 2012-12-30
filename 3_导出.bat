@echo off
@if "%1" == "" goto noparams
@exporter.py %1
@goto end
:noparams
@exporter.py
:end
@pause