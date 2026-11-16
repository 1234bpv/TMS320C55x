@echo off
setlocal
REM ---------------------------------------------------------------------------
REM build_dcd_stub.cmd - build a DCD-ONLY DOFF (no code) for our node's UUID.
REM
REM Why: ord26 in bridgeapi does two things in order - (1) parse the file's
REM .dcd_register / .<UUID> sections and register them with the driver, then
REM (2) load the file onto the DSP as a processor image. On the device it
REM survives step 1 and kills the kernel in step 2 whenever the file is a
REM dynamic node library (ours AND the stock pingdyn - so it is not our DOFF).
REM
REM This stub carries the SAME DCD sections as the real node but no allocated
REM code at all, so step 2 has nothing to download. If ord26 returns cleanly
REM and ord6(our UUID) then finds the node, we have both registered our UUID
REM and proved the crash is tied to loading a node's code through ord26.
REM
REM Comments ASCII on purpose (cmd + old TI tools).
REM ---------------------------------------------------------------------------

call "%~dp0env.cmd"
if errorlevel 1 exit /b 1
set WORK=%TEMP%\dsptest_c55stub
set OUT=%PROJ%\out\dsp

if not exist "%CGT%\bin\cl55.exe" (echo [stub] C5500 CGT not found & exit /b 1)
set PATH=%CGT%\bin;%PATH%

if not exist "%WORK%" mkdir "%WORK%"
copy /y "%PROJ%\src\dsp\bench_dcd.s55" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\bench_node.lcf" "%WORK%" >nul
pushd "%WORK%"

echo [stub] assemble DCD record only
call cl55 -v5510 --symdebug:none --mem_model:data=large -c bench_dcd.s55
if errorlevel 1 (popd & echo [stub] compile FAILED & exit /b 1)

echo [stub] partial link -^> benchdcd.x55
call lnk55 -r -cr -o benchdcd.x55 bench_dcd.obj bench_node.lcf
if errorlevel 1 (popd & echo [stub] link FAILED & exit /b 1)

if not exist "%OUT%" mkdir "%OUT%"
echo [stub] DOFF convert -^> benchdcd.dll55l
call "%DSP_DOFFBUILD%\bin\dllcreate.exe" benchdcd.x55 -o=benchdcd.dll55l
if errorlevel 1 (popd & echo [stub] dllcreate FAILED & exit /b 1)
copy /y benchdcd.dll55l "%OUT%" >nul
echo [stub] -^> %OUT%\benchdcd.dll55l
popd
exit /b 0
