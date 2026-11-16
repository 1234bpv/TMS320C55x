@echo off
setlocal
call "%~dp0env.cmd"
if errorlevel 1 exit /b 1
if not exist "%PROJ%\out\mdec-kernel" mkdir "%PROJ%\out\mdec-kernel"
pushd "%PROJ%\out\mdec-kernel"
del /q kernel_c55.obj kernel_arm343.o kernel_arm463.o mdec_probe463.lib 2>nul
"%CGT%\bin\cl55.exe" -v5510 -o3 --symdebug:none --keep_asm --mem_model:data=large -I"%CGT%\include" -c "%PROJ%\src\mdec\kernel_c55.c"
if errorlevel 1 (popd & exit /b 1)
"%TCROOT%\CSL_Arm_Toolchain\bin\arm-none-symbianelf-gcc.exe" -O2 -march=armv6 -mtune=arm1136j-s -fomit-frame-pointer -fno-strict-aliasing -c "%PROJ%\src\mdec\kernel_arm.c" -o kernel_arm343.o
if errorlevel 1 (popd & exit /b 1)
REM Match current emulator core's optimization and architecture flags.
"%TCROOT%\gcce\arm-2012.03\bin\arm-none-symbianelf-gcc.exe" -O2 -march=armv6 -mtune=arm1136j-s -fno-exceptions -fshort-wchar -Dmdec_kernel_process=mdec_kernel_process_arm463 -c "%PROJ%\src\mdec\kernel_arm.c" -o kernel_arm463.o
if errorlevel 1 (popd & exit /b 1)
REM Match the emulator's bridge to the old Symbian EABI4 linker.
"%TCROOT%\gcce\arm-2012.03\bin\arm-none-symbianelf-objcopy.exe" -R .ARM.attributes kernel_arm463.o
if errorlevel 1 (popd & exit /b 1)
powershell -NoProfile -Command "$p='kernel_arm463.o'; $b=[IO.File]::ReadAllBytes($p); if ($b[0] -ne 127 -or $b[4] -ne 1) { exit 1 }; $b[0x24]=0; $b[0x25]=0; $b[0x26]=0; $b[0x27]=4; [IO.File]::WriteAllBytes($p,$b)"
if errorlevel 1 (popd & exit /b 1)
"%TCROOT%\CSL_Arm_Toolchain\bin\arm-none-symbianelf-ar.exe" rc mdec_probe463.lib kernel_arm463.o
if errorlevel 1 (popd & exit /b 1)
"%TCROOT%\CSL_Arm_Toolchain\bin\arm-none-symbianelf-ranlib.exe" mdec_probe463.lib
if errorlevel 1 (popd & exit /b 1)
popd
exit /b 0
