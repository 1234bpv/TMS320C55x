@echo off
setlocal
call "%~dp0env.cmd"
if errorlevel 1 exit /b 1
set WORK=%TEMP%\c55stream_node
set OUT=%PROJ%\out\dsp
set DEFINES=
set EXTRA_SOURCE=
set EXTRA_OBJECT=
if /i "%~1"=="run-stop" goto :variant_ok
if /i "%~1"=="dmm-ring" goto :variant_ok
if /i "%~1"=="dmm-ring-dcr" goto :variant_ok
if /i "%~1"=="dmm-ring-wsola" goto :variant_ok
if /i "%~1"=="dmm-ring-window" goto :variant_ok
if /i "%~1"=="dmm-ring-mdec" goto :variant_ok
if /i "%~1"=="dmm-ring-spu" goto :variant_ok
if /i "%~1"=="run-message-diag" goto :variant_ok
if /i "%~1"=="run-exit-diag" goto :variant_ok
if /i "%~1"=="worker-message" goto :variant_ok
if not "%~1"=="" if /i not "%~1"=="smoke" if /i not "%~1"=="rms" if /i not "%~1"=="messages" if /i not "%~1"=="messages-bare" if /i not "%~1"=="message-stages" if /i not "%~1"=="worker-once" if /i not "%~1"=="worker-parked" if /i not "%~1"=="worker-stream" if /i not "%~1"=="resident-check" if /i not "%~1"=="resident-phase" (
  echo Usage: build_stream_node.cmd [run-stop^|smoke^|rms^|messages^|messages-bare^|message-stages^|worker-once^|worker-parked^|worker-stream^|resident-check^|resident-phase]
  exit /b 2
)
:variant_ok
if /i "%~1"=="run-stop" set DEFINES=-DEXEC_RUN_STOP=1
if /i "%~1"=="dmm-ring" set DEFINES=-DEXEC_RUN_STOP=1 -DEXEC_DMM_RING=1
if /i "%~1"=="dmm-ring-window" set DEFINES=-DEXEC_RUN_STOP=1 -DEXEC_DMM_RING=1
if /i "%~1"=="dmm-ring-dcr" set DEFINES=-DEXEC_RUN_STOP=1 -DEXEC_DMM_RING=1 -DEXEC_DMM_DCR_READ=1
if /i "%~1"=="dmm-ring-dcr" set EXTRA_SOURCE=dcr_read.s55
if /i "%~1"=="dmm-ring-dcr" set EXTRA_OBJECT=dcr_read.obj
if /i "%~1"=="dmm-ring-wsola" set DEFINES=-DEXEC_RUN_STOP=1 -DEXEC_DMM_RING=1 -DEXEC_DMM_DCR_READ=1 -DEXEC_DMM_WSOLA=1
if /i "%~1"=="dmm-ring-wsola" set EXTRA_SOURCE=dcr_read.s55
if /i "%~1"=="dmm-ring-wsola" set EXTRA_OBJECT=dcr_read.obj
if /i "%~1"=="dmm-ring-mdec" set DEFINES=-DEXEC_RUN_STOP=1 -DEXEC_DMM_RING=1 -DEXEC_DMM_DCR_READ=1 -DEXEC_DMM_MDEC=1 -DMDEC_C55_TARGET=1
if /i "%~1"=="dmm-ring-mdec" set EXTRA_SOURCE=dcr_read.s55 mdec\kernel_c55.c
if /i "%~1"=="dmm-ring-mdec" set EXTRA_OBJECT=dcr_read.obj kernel_c55.obj
if /i "%~1"=="dmm-ring-spu" set DEFINES=-DEXEC_RUN_STOP=1 -DEXEC_DMM_RING=1 -DEXEC_DMM_DCR_READ=1 -DEXEC_DMM_SPU=1
if /i "%~1"=="dmm-ring-spu" set EXTRA_SOURCE=dcr_read.s55
if /i "%~1"=="dmm-ring-spu" set EXTRA_OBJECT=dcr_read.obj
if /i "%~1"=="run-message-diag" set DEFINES=-DEXEC_MSG_STAGES=1
if /i "%~1"=="run-exit-diag" set DEFINES=-DEXEC_EXIT_DIAG=1
if /i "%~1"=="smoke" set DEFINES=-DEXEC_SMOKE=1
if /i "%~1"=="rms" set DEFINES=-DEXEC_RMS_WAIT=1
if /i "%~1"=="messages" set DEFINES=-DEXEC_MSG_DIAG=1
if /i "%~1"=="messages-bare" set DEFINES=-DEXEC_MSG_DIAG=1 -DMSG_BARE_NODE=1
if /i "%~1"=="message-stages" set DEFINES=-DEXEC_MSG_STAGES=1
if /i "%~1"=="worker-once" set DEFINES=-DCREATE_WORKER_ONCE=1
if /i "%~1"=="worker-parked" set DEFINES=-DCREATE_WORKER_PARKED=1
if /i "%~1"=="worker-stream" set DEFINES=-DCREATE_STREAM_WORKER=1
if /i "%~1"=="worker-message" set DEFINES=-DCREATE_STREAM_WORKER=1 -DCREATE_WORKER_MSG=1
if /i "%~1"=="resident-check" set DEFINES=-DCREATE_RESIDENT_CHECK=1
if /i "%~1"=="resident-phase" set DEFINES=-DCREATE_RESIDENT_CHECK=1
if /i "%~1"=="resident-check" set EXTRA_SOURCE=resident_stamp.s55
if /i "%~1"=="resident-phase" set EXTRA_SOURCE=resident_stamp.s55
if "%EXTRA_SOURCE%"=="resident_stamp.s55" set EXTRA_OBJECT=resident_stamp.obj
if not exist "%WORK%" mkdir "%WORK%"
if not exist "%WORK%\mdec" mkdir "%WORK%\mdec"
copy /y "%PROJ%\src\mdec\kernel*" "%WORK%\mdec" >nul
copy /y "%PROJ%\src\dsp\stream*" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\spu_mix_ring.inc" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\node.h" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\bios_task.h" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\resident_stamp.s55" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\dcr_read.s55" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\bench_dsp.c" "%WORK%" >nul
copy /y "%PROJ%\src\dsp\wsola_dsp.c" "%WORK%" >nul
pushd "%WORK%"
if /i "%~1"=="messages-bare" copy /y stream_message_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="resident-check" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="worker-parked" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="worker-stream" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="worker-message" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="run-stop" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="dmm-ring" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="dmm-ring-dcr" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="dmm-ring-wsola" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="dmm-ring-window" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="dmm-ring-mdec" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="dmm-ring-spu" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="run-message-diag" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
if /i "%~1"=="run-exit-diag" copy /y stream_resident_dcd.s55 stream_dcd.s55 >nul
"%CGT%\bin\cl55.exe" -v5510 -o3 --symdebug:none --keep_asm --mem_model:data=large %DEFINES% -I"%CGT%\include" -c stream_node.c bench_dsp.c wsola_dsp.c stream_dcd.s55 %EXTRA_SOURCE%
if errorlevel 1 (popd & exit /b 1)
"%CGT%\bin\lnk55.exe" -r -cr --localize=$bss -o stream.x55 stream_node.obj bench_dsp.obj wsola_dsp.obj stream_dcd.obj %EXTRA_OBJECT% stream_node.lcf
if errorlevel 1 (popd & exit /b 1)
"%DSP_DOFFBUILD%\bin\dllcreate.exe" stream.x55 -o=c55stream.dll55l
if errorlevel 1 (popd & exit /b 1)
if not exist "%OUT%" mkdir "%OUT%"
copy /y c55stream.dll55l "%OUT%" >nul
copy /y stream.x55 "%OUT%" >nul
copy /y stream_node.asm "%OUT%" >nul
copy /y wsola_dsp.asm "%OUT%" >nul
copy /y bench_dsp.asm "%OUT%" >nul
if /i "%~1"=="dmm-ring" (
  copy /y c55stream.dll55l "%OUT%\c55stream-dmm-ring.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-dmm-ring.asm" >nul
)
if /i "%~1"=="dmm-ring-dcr" (
  copy /y c55stream.dll55l "%OUT%\c55stream-dmm-ring-dcr.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-dmm-ring-dcr.asm" >nul
)
if /i "%~1"=="dmm-ring-window" (
  copy /y c55stream.dll55l "%OUT%\c55stream-dmm-ring-window.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-dmm-ring-window.asm" >nul
)
if /i "%~1"=="dmm-ring-mdec" (
  copy /y c55stream.dll55l "%OUT%\c55stream-dmm-ring-mdec.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-dmm-ring-mdec.asm" >nul
  copy /y kernel_c55.asm "%OUT%\kernel_c55-mdec.asm" >nul
)
if /i "%~1"=="dmm-ring-spu" (
  copy /y c55stream.dll55l "%OUT%\c55stream-dmm-ring-spu.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-dmm-ring-spu.asm" >nul
)
if /i "%~1"=="dmm-ring-wsola" (
  copy /y c55stream.dll55l "%OUT%\c55stream-dmm-ring-wsola.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-dmm-ring-wsola.asm" >nul
)
if /i "%~1"=="run-stop" (
  copy /y c55stream.dll55l "%OUT%\c55stream-run-stop.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-run-stop.asm" >nul
)
if /i "%~1"=="worker-message" (
  copy /y c55stream.dll55l "%OUT%\c55stream-worker-message.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-worker-message.asm" >nul
)
if /i "%~1"=="run-message-diag" (
  copy /y c55stream.dll55l "%OUT%\c55stream-run-message-diag.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-run-message-diag.asm" >nul
)
if /i "%~1"=="run-exit-diag" (
  copy /y c55stream.dll55l "%OUT%\c55stream-run-exit-diag.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-run-exit-diag.asm" >nul
)
if /i "%~1"=="smoke" copy /y c55stream.dll55l "%OUT%\c55stream-smoke.dll55l" >nul
if /i "%~1"=="rms" (
  copy /y c55stream.dll55l "%OUT%\c55stream-rms.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-rms.asm" >nul
)
if /i "%~1"=="messages" (
  copy /y c55stream.dll55l "%OUT%\c55stream-messages.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-messages.asm" >nul
)
if /i "%~1"=="messages-bare" (
  copy /y c55stream.dll55l "%OUT%\c55stream-messages-bare.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-messages-bare.asm" >nul
)
if /i "%~1"=="message-stages" (
  copy /y c55stream.dll55l "%OUT%\c55stream-message-stages.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-message-stages.asm" >nul
)
if /i "%~1"=="worker-once" (
  copy /y c55stream.dll55l "%OUT%\c55stream-worker-once.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-worker-once.asm" >nul
)
if /i "%~1"=="worker-parked" (
  copy /y c55stream.dll55l "%OUT%\c55stream-worker-parked.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-worker-parked.asm" >nul
)
if /i "%~1"=="worker-stream" (
  copy /y c55stream.dll55l "%OUT%\c55stream-worker-stream.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-worker-stream.asm" >nul
)
if /i "%~1"=="resident-check" (
  copy /y c55stream.dll55l "%OUT%\c55stream-resident-check.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-resident-check.asm" >nul
)
if /i "%~1"=="resident-phase" (
  copy /y c55stream.dll55l "%OUT%\c55stream-resident-phase.dll55l" >nul
  copy /y stream_node.asm "%OUT%\stream_node-resident-phase.asm" >nul
)
popd
exit /b 0
