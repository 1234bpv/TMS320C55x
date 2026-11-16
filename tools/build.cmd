@echo off
setlocal
REM ---------------------------------------------------------------------------
REM build.cmd - build dsptest.exe (C55x-vs-ARM benchmark host).
REM
REM   build.cmd                  build only
REM   build.cmd run [ip] [args]  build, push to the phone, run it, pull the log
REM
REM Example: build.cmd run 192.168.1.5
REM
REM No SIS needed: the daemon drops the EXE straight into E:\sys\bin and
REM refreshes the SHA-1 in C:\sys\hash - that digest is what makes the loader
REM accept the binary with its declared capabilities. (Same flow as the sibling
REM SymbianOverclock/SymbianDeployDaemon projects.)
REM
REM EPOCROOT carries no drive letter: build on the discovered SDK drive.
REM Perl must be < 5.22: E32Plat.pm uses defined(%hash).
REM
REM Comments here stay ASCII on purpose - cmd mangles UTF-8 in batch files.
REM ---------------------------------------------------------------------------

REM The SDK build chain cannot handle a space in the project path: abld hands
REM makmake an unquoted path, so "TMS320C55x test\group\DSPTEST" arrives as two
REM arguments and makmake just prints its usage banner (no makefile, then a
REM confusing "No rule to make target"). We therefore build through a junction
REM with a space-free name that points at this very directory - same sources,
REM same outputs, just a name the 2007 Perl tooling can parse.
REM
REM The junction lives OUTSIDE the projects tree and is removed again at the end
REM of the build, so it never shows up as a second project folder. It must sit
REM on the SDK drive because EPOCROOT has no drive letter and resolves
REM against the current drive.
call "%~dp0env.cmd"
if errorlevel 1 exit /b 1
call "%~dp0build_mdec_kernel.cmd"
if errorlevel 1 exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_mdec_library.ps1" -SdkRoot "%SDKROOT%"
if errorlevel 1 exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_alias.ps1" -Action Create -Alias "%PROJLINK%" -Project "%PROJ%"
if errorlevel 1 exit /b 1

REM Delete the target first. ABLD.BAT can return 0 even when make failed, and
REM then a STALE exe from an earlier build gets deployed - the phone silently
REM runs code that does not match the source. Seen once: the compile errored
REM out, "built ->" was still printed, and the run used the previous binary.
del /q "%SDKROOT%\Epoc32\release\gcce\urel\dsptest.exe" 2>nul
del /q "%SDKROOT%\Epoc32\release\gcce\urel\c55stream.exe" 2>nul
REM MMP compiler-option edits do not invalidate cached objects in this SDK.
REM Recompile these two research sources so an old ARMv5 baseline is not reused.
del /q "%SDKROOT%\Epoc32\BUILD\symbuild\c55x\group\C55STREAM\GCCE\UREL\c55stream.o" 2>nul
del /q "%SDKROOT%\Epoc32\BUILD\symbuild\c55x\group\C55STREAM\GCCE\UREL\wsola_reference.o" 2>nul
del /q "%SDKROOT%\Epoc32\BUILD\symbuild\c55x\group\C55STREAM\GCCE\UREL\kernel_arm.o" 2>nul
del /q "%SDKROOT%\Epoc32\BUILD\symbuild\c55x\group\C55STREAM\GCCE\UREL\mix_arm.o" 2>nul
del /q "%SDKROOT%\Epoc32\BUILD\symbuild\c55x\group\C55STREAM\GCCE\UREL\mix_job_arm.o" 2>nul
del /q "%SDKROOT%\Epoc32\BUILD\symbuild\c55x\group\C55STREAM\GCCE\UREL\kernel.o" 2>nul

pushd "%PROJLINK%\group"
call bldmake bldfiles
if errorlevel 1 (popd & goto :build_failed)
call .\ABLD.BAT build gcce urel
if errorlevel 1 (popd & goto :build_failed)
popd

REM Drop the build alias again (rmdir without /s removes only the junction,
REM never the files it points at).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_alias.ps1" -Action Remove -Alias "%PROJLINK%" -Project "%PROJ%"
if errorlevel 1 exit /b 1

set EXE=%SDKROOT%\Epoc32\release\gcce\urel\dsptest.exe
if not exist "%EXE%" (echo [dsptest] no binary at %EXE% & exit /b 1)
if not exist "%PROJ%\out\arm" mkdir "%PROJ%\out\arm"
copy /y "%EXE%" "%PROJ%\out\arm\dsptest.exe" >nul
if not exist "%SDKROOT%\Epoc32\release\gcce\urel\c55stream.exe" exit /b 1
copy /y "%SDKROOT%\Epoc32\release\gcce\urel\c55stream.exe" "%PROJ%\out\arm" >nul
echo [dsptest] built -^> %EXE%

if /i not "%~1"=="run" exit /b 0

set DIP=%~2
if "%DIP%"=="" (echo [dsptest] run requires an explicit N95 IP & exit /b 1)
set ARGS=%~3
set CMDLINE=E:\sys\bin\dsptest.exe
if not "%ARGS%"=="" set CMDLINE=E:\sys\bin\dsptest.exe %ARGS%

REM The DSP node has to be on the phone before the 'load' probe can hand its
REM path to bridgeapi ord26. It is plain data (no hash grant needed - only
REM executables are hash-checked), so a separate PUT is enough. Skipped if the
REM node has not been built yet.
REM DCD-only stub (tools\build_dcd_stub.cmd) - registers our node's UUID
REM without any downloadable code.
set STUB=%PROJ%\out\dsp\benchdcdx.dll55l
if exist "%STUB%" (
  python "%PROJ%\tools\strict_net.py" --ip "%DIP%" --device n95 --put "%STUB%" "E:\benchdcdx.dll55l"
  if errorlevel 1 exit /b 1
)

set NODE=%PROJ%\out\dsp\bench.dll55l
if exist "%NODE%" (
  python "%PROJ%\tools\strict_net.py" --ip "%DIP%" --device n95 --put "%NODE%" "E:\bench.dll55l"
  if errorlevel 1 exit /b 1
) else (
  echo [dsptest] no DSP node at "%NODE%" - run tools\build_dsp_node.cmd first
)

python "%PROJ%\tools\strict_net.py" --ip "%DIP%" --device n95 --timeout 185 ^
  --put "%EXE%" "E:\sys\bin\dsptest.exe" --hash-remote "C:\sys\hash\dsptest.exe" ^
  --cmd "EXEC 180000 %CMDLINE%" --require-exit-zero ^
  --get "E:\dsptest.log" "%PROJ%\out\dsptest.log"
if errorlevel 1 (echo [dsptest] deploy/run FAILED & exit /b 1)
echo [dsptest] log -^> %PROJ%\out\dsptest.log
exit /b 0

:build_failed
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_alias.ps1" -Action Remove -Alias "%PROJLINK%" -Project "%PROJ%"
echo [dsptest] build FAILED
exit /b 1
