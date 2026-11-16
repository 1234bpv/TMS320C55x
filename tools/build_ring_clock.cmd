@echo off
setlocal
call "%~dp0env.cmd"
if errorlevel 1 exit /b 1
set "CLOCKSTAGE=%PROJ%\out\ringclock-build"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_alias.ps1" -Action Create -Alias "%PROJLINK%" -Project "%CLOCKSTAGE%"
if errorlevel 1 exit /b 1
pushd "%PROJLINK%\group"
call bldmake bldfiles
if errorlevel 1 (popd & goto :failed)
call .\ABLD.BAT reallyclean gcce urel
call .\ABLD.BAT build gcce urel
if errorlevel 1 (popd & goto :failed)
popd
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_alias.ps1" -Action Remove -Alias "%PROJLINK%" -Project "%CLOCKSTAGE%"
if errorlevel 1 exit /b 1
if not exist "%SDKROOT%\Epoc32\release\gcce\urel\ringclock.exe" exit /b 1
copy /y "%SDKROOT%\Epoc32\release\gcce\urel\ringclock.exe" "%PROJ%\out\arm\ringclock.exe" >nul
exit /b 0
:failed
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_alias.ps1" -Action Remove -Alias "%PROJLINK%" -Project "%CLOCKSTAGE%"
exit /b 1
