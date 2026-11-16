@echo off
setlocal
REM ---------------------------------------------------------------------------
REM build_dsp_node.cmd - build the C55x dspbridge benchmark node.
REM
REM Pipeline (mirrors felipec/dsp-dummy Makefile, C55x variant):
REM   cl55  -c            : compile kernels + node to TI-COFF .obj
REM   asm55               : assemble the DCD registration record
REM   lnk55 -r -cr        : partial link to relocatable COFF  bench.x55
REM   DLLcreate           : convert COFF -> DOFF node          bench.dll55l
REM
REM Do NOT pass DLLcreate the stock -e entries file (doffbuild/entries/
REM bios_entries.ent): it localizes every symbol it does not name, which
REM includes our three phase functions - RMS then cannot find them by the
REM names in the DCD record and the node is dead weight. Debug sections are
REM kept out with --symdebug:none at compile time instead.
REM
REM All three steps run natively on Windows (verified). dllcreate.exe comes from
REM the doffbuild package (bridge-tools.tar in kpykc/userspace-dspbridge, a
REM mirror of dev.omapzoom.org tidspbridge). DSP_DOFFBUILD defaults to the
REM extracted copy under toolchain\; override it if you keep it elsewhere.
REM
REM Old cl55 dislikes spaces in the CWD/source paths, so we build in an ASCII
REM temp dir and copy artifacts back to out\dsp.
REM
REM Comments ASCII on purpose (cmd + old TI tools).
REM ---------------------------------------------------------------------------

call "%~dp0env.cmd"
if errorlevel 1 exit /b 1
set WORK=%TEMP%\dsptest_c55node
set OUT=%PROJ%\out\dsp

if not exist "%CGT%\bin\cl55.exe" (echo [node] C5500 CGT not found at "%CGT%" & exit /b 1)
set PATH=%CGT%\bin;%PATH%

if not exist "%WORK%" mkdir "%WORK%"
copy /y "%PROJ%\src\dsp\*.c" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\*.h" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\*.s55" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\*.lcf" "%WORK%" >nul
pushd "%WORK%"

REM The .s55 goes through cl55 as well, not asm55 directly: asm55 v4.4.1 says
REM "designed to be invoked by the compiler" and, called bare, stamps the
REM object with Tag_Memory_Model=small, which lnk55 then refuses to combine
REM with the large-model C objects.
echo [node] compile (large data model) + assemble DCD record
REM BENCH_CREATE_REPS: how many times the create phase runs the Q15 dot
REM kernel on the DSP. The ARM side times DoControl(5), so two builds with
REM different rep counts give a differential measurement that cancels the
REM fixed node-load overhead. First arg to this script overrides it.
if "%~1"=="" (set CREPS=0) else (set CREPS=%~1)
REM Second arg selects the workload: 0=none 1=Q15dot 2=int32 3=fp32 4=branch
REM   5=MAC without memory  6=int32 manual  7=fp32 manual
REM   8=division via compiler  9=division manual
REM   10=DSP clock probe via CLK_gethtime  11=read _BRIDGEINIT_DSP_FREQ
if "%~2"=="" (set CWL=1) else (set CWL=%~2)
REM Third arg: BENCH_PROBE. Workload 10 (clock probe): 0 = measure only,
REM 1 = additionally spin (ticks>>10) more reps so the tick count shows up
REM as extra wall time on the ARM side. Workload 11 (DSP frequency):
REM 0 = baseline, 2 = calibration (fixed 50000 reps), 1 = value>>2 reps.
if "%~3"=="" (set CPRB=0) else (set CPRB=%~3)
REM Fourth arg: BENCH_CREATE_N, the working vector length. It decides which DSP
REM memory segment the loader puts .bss in - the DYN_DARAM dynamic heap in this
REM base image is only 256 words (see the table in bench_node.c), so anything
REM larger falls through to DYN_SARAM, which is single-access.
if "%~4"=="" (set CN=1024) else (set CN=%~4)
REM Fifth arg: data segment id, low byte of DCD field 30. 0=DARAM 1=SARAM
REM 2=EXTERNAL 3=SRAM. Default 0, as every Nokia and TI node uses.
if "%~5"=="" (set CSEG=0) else (set CSEG=%~5)
if not "%CSEG%"=="0" powershell -NoProfile -Command "(Get-Content '%WORK%\bench_dcd.s55' -Raw) -replace '0ff3f3f00H','0ff3f3f0%CSEG%H' | Set-Content -NoNewline '%WORK%\bench_dcd.s55'"
call cl55 -v5510 -o3 --symdebug:none --mem_model:data=large -DBENCH_CREATE_REPS=%CREPS% -DBENCH_WORKLOAD=%CWL% -DBENCH_PROBE=%CPRB% -DBENCH_CREATE_N=%CN% -I"%CGT%\include" -c bench_dsp.c bench_node.c bench_dcd.s55
if errorlevel 1 (popd & echo [node] compile FAILED & exit /b 1)

echo [node] partial link -^> bench.x55
call lnk55 -r -cr --localize=$bss -o bench.x55 bench_dsp.obj bench_node.obj bench_dcd.obj bench_node.lcf
if errorlevel 1 (popd & echo [node] link FAILED & exit /b 1)

if not exist "%OUT%" mkdir "%OUT%"
copy /y bench.x55 "%OUT%" >nul
echo [node] relocatable COFF -^> %OUT%\bench.x55

if not exist "%DSP_DOFFBUILD%\bin\dllcreate.exe" goto :no_doff

echo [node] DOFF convert -^> bench.dll55l
call "%DSP_DOFFBUILD%\bin\dllcreate.exe" bench.x55 -o=bench.dll55l
if errorlevel 1 (popd & echo [node] dllcreate FAILED & exit /b 1)
copy /y bench.dll55l "%OUT%" >nul
echo [node] DOFF node -^> %OUT%\bench.dll55l
popd
exit /b 0

:no_doff
echo [node] dllcreate.exe not found under "%DSP_DOFFBUILD%\bin".
echo [node] Extract doffbuild from bridge-tools.tar in kpykc/userspace-dspbridge,
echo [node] or set DSP_DOFFBUILD to its root. Stopped after bench.x55.
popd
exit /b 1
