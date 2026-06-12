@echo off
setlocal
set "DLDIR=E:\Users\Martin\Documents\GitHub\PrusaSlicer-SiliconeLDM\deps\build\_download"
set "PROXY=--socks5 127.0.0.1:10808"

cd /d "%DLDIR%"

echo Downloading dependencies via SOCKS5 proxy...
echo.

call :dl nlopt-v2.5.0.tar.gz "https://github.com/stevengj/nlopt/archive/v2.5.0.tar.gz"
call :dl Catch2-v3.8.0.zip "https://github.com/catchorg/Catch2/archive/refs/tags/v3.8.0.zip"
call :dl json-v3.12.0.zip "https://github.com/nlohmann/json/archive/refs/tags/v3.12.0.zip"
call :dl heatshrink-v0.4.1.zip "https://github.com/atomicobject/heatshrink/archive/refs/tags/v0.4.1.zip"
call :dl oneTBB-v2021.5.0.zip "https://github.com/oneapi-src/oneTBB/archive/refs/tags/v2021.5.0.zip"
call :dl z3-4.15.1.zip "https://github.com/Z3Prover/z3/archive/refs/tags/z3-4.15.1.zip"
call :dl glew-2.2.0.zip "https://sourceforge.net/projects/glew/files/glew/2.2.0/glew-2.2.0.zip"
call :dl eigen-3.3.7.zip "https://gitlab.com/libeigen/eigen/-/archive/3.3.7/eigen-3.3.7.zip"
call :dl expat-R_2_4_3.zip "https://github.com/libexpat/libexpat/archive/refs/tags/R_2_4_3.zip"
call :dl cereal-v1.3.0.zip "https://github.com/USCiLab/cereal/archive/refs/tags/v1.3.0.zip"
call :dl nanosvg-abcd277.zip "https://github.com/fltk/nanosvg/archive/abcd277ea45e9098bed752cf9c6875b533c0892f.zip"

echo.
echo Done.
goto :eof

:dl
if exist "%DLDIR%\%~1" (
    echo [SKIP] %~1 (already exists^)
) else (
    echo [DOWNLOAD] %~1 ...
    curl %PROXY% -L -o "%~1" "%~2" --max-time 180 -s 2>&1 && echo   [OK] || echo   [FAIL]
)
goto :eof
