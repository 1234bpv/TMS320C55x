@echo off
REM Called within the caller's SETLOCAL; discovers this shared checkout.
for %%I in ("%~dp0..") do set "PROJ=%%~fI"
for %%I in ("%PROJ%\..") do set "SYMBIANROOT=%%~fI"
set "SDKROOT=%SYMBIANROOT%\S60_3rd_FP1"
set "TCROOT=%SYMBIANROOT%\toolchain"
set "DAEMON=%SYMBIANROOT%\SymbianDeployDaemon"
for %%I in ("%SDKROOT%") do set "EPOCROOT=%%~pnxI\"
for %%I in ("%SDKROOT%") do set "SDKDRIVE=%%~dI"
set "PROJLINK=%SDKDRIVE%\symbuild\c55x"
set "LC_ALL=C"
set "PATH=%TCROOT%\perl\perl\bin;%SDKROOT%\Epoc32\tools;%TCROOT%\cppshim\gcc\bin;%TCROOT%\CSL_Arm_Toolchain\bin;%SDKROOT%\Epoc32\gcc\bin;%PATH%"
if not defined DSP_DOFFBUILD set "DSP_DOFFBUILD=%TCROOT%\ti\dspbridge\dsp\doffbuild"
REM Explicit DSP_CGT wins, then PATH, then the original TI install on any drive.
if defined DSP_CGT goto :cgt_found
for /f "delims=" %%I in ('where cl55.exe 2^>nul') do if not defined DSP_CGT for %%J in ("%%~dpI..") do set "DSP_CGT=%%~fJ"
for %%D in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do if not defined DSP_CGT if exist "%%D:\Program Files (x86)\Texas Instruments\C5500 Code Generation Tools 4.4.1\bin\cl55.exe" set "DSP_CGT=%%D:\Program Files (x86)\Texas Instruments\C5500 Code Generation Tools 4.4.1"
:cgt_found
set "CGT=%DSP_CGT%"
if defined CGT set "PATH=%CGT%\bin;%PATH%"
if /i not "%~1"=="print" exit /b 0
echo PROJ=%PROJ%
echo SDKROOT=%SDKROOT%
echo TCROOT=%TCROOT%
echo DAEMON=%DAEMON%
echo EPOCROOT=%EPOCROOT%
echo PROJLINK=%PROJLINK%
echo DSP_CGT=%DSP_CGT%
echo DSP_DOFFBUILD=%DSP_DOFFBUILD%
exit /b 0
