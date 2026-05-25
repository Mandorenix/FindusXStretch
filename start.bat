@echo off
setlocal enabledelayedexpansion
title FINDUS^>x^<STRETCHING Developer Launcher
set "CLR_RESET="
set "CLR_TITLE="
set "CLR_MENU="
set "CLR_OK="
set "CLR_INFO="
set "CLR_WARN="

goto start

:refresh_status
call :set_python_silent
call :detect_venv
call :read_version_silent
goto :eof

:set_python
set "PYTHON_CMD=python"
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo Kunde inte hitta Python i PATH.
        pause
        goto menu
    )
    set "PYTHON_CMD=py"
)
goto :eof

:set_python_silent
set "PYTHON_CMD=python"
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        set "PYTHON_CMD="
        set "PYTHON_STATUS=%CLR_WARN%Saknas i PATH%CLR_RESET%"
        goto :eof
    )
    set "PYTHON_CMD=py"
)
for /f "delims=" %%v in ('%PYTHON_CMD% --version 2^>nul') do set "PYTHON_STATUS=%CLR_OK%%%v%CLR_RESET%"
goto :eof

:detect_venv
if exist .venv\Scripts\activate.bat (
    set "VENV_STATUS=%CLR_OK%Available (.venv)%CLR_RESET%"
) else (
    set "VENV_STATUS=%CLR_WARN%Saknas%CLR_RESET%"
)
goto :eof

:read_version_silent
set "RELEASE_VERSION="
for /f "tokens=1,2 delims=," %%a in ('findstr /c:"ProductVersion" assets\version_info.txt') do set "RELEASE_VERSION=%%b"
set "RELEASE_VERSION=!RELEASE_VERSION:"=!"
set "RELEASE_VERSION=!RELEASE_VERSION:) =!"
set "RELEASE_VERSION=!RELEASE_VERSION:)=!"
set "RELEASE_VERSION=!RELEASE_VERSION:,=!"
set "RELEASE_VERSION=!RELEASE_VERSION: =!"
if not defined RELEASE_VERSION set "RELEASE_VERSION=0.1.1"
goto :eof

:read_version
call :read_version_silent
echo %CLR_INFO%Version:%CLR_RESET%   !RELEASE_VERSION!
goto :eof

:stamp_now
set "RELEASE_STAMP=%date% %time:~0,8%"
goto :eof

:bump_patch_version_no_pause
call :read_version_silent
for /f "tokens=1-3 delims=." %%a in ("!RELEASE_VERSION!") do (
    set "VERSION_MAJOR=%%a"
    set "VERSION_MINOR=%%b"
    set "VERSION_PATCH=%%c"
)
if not defined VERSION_MAJOR exit /b 1
if not defined VERSION_MINOR exit /b 1
if not defined VERSION_PATCH exit /b 1
set /a VERSION_PATCH+=1
set "RELEASE_VERSION=!VERSION_MAJOR!.!VERSION_MINOR!.!VERSION_PATCH!"
powershell -NoProfile -Command "$path='assets\\version_info.txt'; $version='!RELEASE_VERSION!'; $parts=$version.Split('.'); $quad='{0}, {1}, {2}, 0' -f $parts[0],$parts[1],$parts[2]; $content=Get-Content $path; $updated=$content ^| ForEach-Object { if ($_ -match '^\s*filevers=\(') { '    filevers=(' + $quad + '),' } elseif ($_ -match '^\s*prodvers=\(') { '    prodvers=(' + $quad + '),' } elseif ($_ -like '*StringStruct(""FileVersion""*') { '            StringStruct(""FileVersion"", ""' + $version + '""),' } elseif ($_ -like '*StringStruct(""ProductVersion""*') { '            StringStruct(""ProductVersion"", ""' + $version + '""),' } else { $_ } }; Set-Content $path $updated -Encoding UTF8"
if %errorlevel% neq 0 exit /b 1
exit /b 0

:bump_minor_version_no_pause
call :read_version_silent
for /f "tokens=1-3 delims=." %%a in ("!RELEASE_VERSION!") do (
    set "VERSION_MAJOR=%%a"
    set "VERSION_MINOR=%%b"
    set "VERSION_PATCH=%%c"
)
if not defined VERSION_MAJOR exit /b 1
if not defined VERSION_MINOR exit /b 1
set /a VERSION_MINOR+=1
set "VERSION_PATCH=0"
set "RELEASE_VERSION=!VERSION_MAJOR!.!VERSION_MINOR!.!VERSION_PATCH!"
powershell -NoProfile -Command "$path='assets\\version_info.txt'; $version='!RELEASE_VERSION!'; $parts=$version.Split('.'); $quad='{0}, {1}, {2}, 0' -f $parts[0],$parts[1],$parts[2]; $content=Get-Content $path; $updated=$content ^| ForEach-Object { if ($_ -match '^\s*filevers=\(') { '    filevers=(' + $quad + '),' } elseif ($_ -match '^\s*prodvers=\(') { '    prodvers=(' + $quad + '),' } elseif ($_ -like '*StringStruct(""FileVersion""*') { '            StringStruct(""FileVersion"", ""' + $version + '""),' } elseif ($_ -like '*StringStruct(""ProductVersion""*') { '            StringStruct(""ProductVersion"", ""' + $version + '""),' } else { $_ } }; Set-Content $path $updated -Encoding UTF8"
if %errorlevel% neq 0 exit /b 1
exit /b 0

:write_release_log_no_pause
if not exist dist\release mkdir dist\release
call :stamp_now
>> dist\release\release_log.txt echo [!RELEASE_STAMP!] version !RELEASE_VERSION!
>> dist\release\release_log.txt echo   exe: %cd%\dist\findus_stretching\findus_stretching.exe
>> dist\release\release_log.txt echo   setup: %cd%\dist\installer\findus_stretching_setup_v!RELEASE_VERSION!.exe
>> dist\release\release_log.txt echo   zip: %cd%\dist\release\findus_stretching_v!RELEASE_VERSION!.zip
>> dist\release\release_log.txt echo.
exit /b 0

:write_changelog_no_pause
call :stamp_now
if not exist CHANGELOG_RELEASES.md (
    > CHANGELOG_RELEASES.md echo # Release History
    >> CHANGELOG_RELEASES.md echo.
)
>> CHANGELOG_RELEASES.md echo ## !RELEASE_VERSION! - !RELEASE_STAMP!
>> CHANGELOG_RELEASES.md echo.
>> CHANGELOG_RELEASES.md echo - Built with start.bat automated release flow.
>> CHANGELOG_RELEASES.md echo - Artifacts: `dist\findus_stretching`, `dist\installer`, `dist\release`.
>> CHANGELOG_RELEASES.md echo.
exit /b 0

:copy_latest_release_no_pause
if not exist dist\release mkdir dist\release
copy /y "dist\installer\findus_stretching_setup_v!RELEASE_VERSION!.exe" "dist\release\findus_stretching_setup_latest.exe" >nul
if %errorlevel% neq 0 exit /b 1
copy /y "!ZIP_PATH!" "dist\release\findus_stretching_latest.zip" >nul
if %errorlevel% neq 0 exit /b 1
exit /b 0

:clean_artifacts_no_pause
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
exit /b 0

:start
call :set_python_silent
call :detect_venv
call :read_version_silent

:menu
call :refresh_status
cls
echo %CLR_TITLE%   ====================================================================   %CLR_RESET%
echo %CLR_TITLE%       /\_/\      F I N D U S  ^> x ^<  S T R E T C H I N G             %CLR_RESET%
echo %CLR_TITLE%      ( o.o )     Ambient Drone Workstation ^& Launcher                 %CLR_RESET%
echo %CLR_TITLE%       ^> ^^^<                                                            %CLR_RESET%
echo %CLR_TITLE%   ====================================================================   %CLR_RESET%
echo.
echo %CLR_INFO%   Workspace:%CLR_RESET% %cd%
echo %CLR_INFO%   Python:%CLR_RESET%    !PYTHON_STATUS!
echo %CLR_INFO%   Venv:%CLR_RESET%      !VENV_STATUS!
echo %CLR_INFO%   Version:%CLR_RESET%   !RELEASE_VERSION!
if exist requirements-optional.txt (
    echo %CLR_INFO%   Extras:%CLR_RESET%    %CLR_OK%requirements-optional.txt found%CLR_RESET%
) else (
    echo %CLR_INFO%   Extras:%CLR_RESET%    %CLR_WARN%No optional requirements file found%CLR_RESET%
)
if exist findus_stretching.spec (
    echo %CLR_INFO%   Spec:%CLR_RESET%      %CLR_OK%findus_stretching.spec found%CLR_RESET%
) else (
    echo %CLR_INFO%   Spec:%CLR_RESET%      %CLR_WARN%No spec file found%CLR_RESET%
)
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    echo %CLR_INFO%   Inno:%CLR_RESET%      %CLR_OK%Inno Setup found%CLR_RESET%
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo %CLR_INFO%   Inno:%CLR_RESET%      %CLR_OK%Inno Setup found%CLR_RESET%
) else (
    echo %CLR_INFO%   Inno:%CLR_RESET%      %CLR_WARN%Inno Setup missing%CLR_RESET%
)
echo.
echo %CLR_MENU%   [1]%CLR_RESET% Start app
echo %CLR_MENU%   [2]%CLR_RESET% Quick start ^(install + tests + app^)
echo %CLR_MENU%   [3]%CLR_RESET% Install dependencies
echo %CLR_MENU%   [4]%CLR_RESET% Install recommended extras
echo %CLR_MENU%   [5]%CLR_RESET% Run tests
echo %CLR_MENU%   [6]%CLR_RESET% Create virtual environment ^(.venv^)
echo %CLR_MENU%   [7]%CLR_RESET% Open new shell with active .venv
echo %CLR_MENU%   [8]%CLR_RESET% Python REPL
echo %CLR_MENU%   [9]%CLR_RESET% Compileall check
echo %CLR_MENU%   [10]%CLR_RESET% Build Windows .exe ^(PyInstaller^)
echo %CLR_MENU%   [11]%CLR_RESET% Create release zip
echo %CLR_MENU%   [12]%CLR_RESET% Build Setup.exe ^(Inno Setup^)
echo %CLR_MENU%   [13]%CLR_RESET% Show installed packages
echo %CLR_MENU%   [14]%CLR_RESET% Open project folder in Explorer
echo %CLR_MENU%   [15]%CLR_RESET% Open README
echo %CLR_MENU%   [16]%CLR_RESET% Show recommended extras
echo %CLR_MENU%   [17]%CLR_RESET% Full release ^(bump + tests + exe + setup + zip^)
echo %CLR_MENU%   [18]%CLR_RESET% Clean build artifacts ^(build + dist^)
echo %CLR_MENU%   [19]%CLR_RESET% Minor release ^(minor bump + full release^)
echo %CLR_MENU%   [20]%CLR_RESET% Explain all options
echo %CLR_MENU%   [21]%CLR_RESET% Write diagnostics report
echo %CLR_MENU%   [22]%CLR_RESET% Hard Reset ^(Nuke .venv, caches, build, dist^)
echo %CLR_MENU%   [23]%CLR_RESET% Code Quality Check ^(Ruff Linter^)
echo %CLR_MENU%   [24]%CLR_RESET% Test PWA Light Version ^(http.server^)
echo %CLR_MENU%   [0]%CLR_RESET% Exit
echo.
set /p choice=Choose an option: 

if "%choice%"=="1" goto run_app
if "%choice%"=="2" goto quick_start
if "%choice%"=="3" goto install_deps
if "%choice%"=="4" goto install_optional_deps
if "%choice%"=="5" goto run_tests
if "%choice%"=="6" goto create_venv
if "%choice%"=="7" goto activate_venv
if "%choice%"=="8" goto python_repl
if "%choice%"=="9" goto compile_check
if "%choice%"=="10" goto build_exe
if "%choice%"=="11" goto build_release_zip
if "%choice%"=="12" goto build_installer
if "%choice%"=="13" goto pip_list
if "%choice%"=="14" goto open_explorer
if "%choice%"=="15" goto open_readme
if "%choice%"=="16" goto show_optional_info
if "%choice%"=="17" goto full_release
if "%choice%"=="18" goto clean_artifacts
if "%choice%"=="19" goto minor_release
if "%choice%"=="20" goto show_menu_help
if "%choice%"=="21" goto diagnostics_report
if "%choice%"=="22" goto hard_reset
if "%choice%"=="23" goto code_quality_check
if "%choice%"=="24" goto start_pwa
if "%choice%"=="0" (
    echo %CLR_OK%Goodbye!%CLR_RESET%
    endlocal
    exit /b 0
)

echo.
echo %CLR_WARN%Invalid option.%CLR_RESET%
pause
goto menu

:run_app
call :set_python
echo.
echo %CLR_INFO%Startar appen...%CLR_RESET%
%PYTHON_CMD% app.py
echo.
pause
goto menu

:quick_start
call :set_python
echo.
echo %CLR_INFO%Installerar beroenden...%CLR_RESET%
%PYTHON_CMD% -m pip install -r requirements.txt || goto command_failed
echo.
echo %CLR_INFO%Koer tester...%CLR_RESET%
%PYTHON_CMD% -m pytest -q || goto command_failed
echo.
echo %CLR_OK%Miljoen ser bra ut. Startar appen...%CLR_RESET%
%PYTHON_CMD% app.py
echo.
pause
goto menu

:install_deps
call :set_python
echo.
echo %CLR_INFO%Installerar beroenden fraan requirements.txt...%CLR_RESET%
%PYTHON_CMD% -m pip install -r requirements.txt
echo.
pause
goto menu

:install_optional_deps
call :set_python
if not exist requirements-optional.txt (
    echo.
    echo %CLR_WARN%requirements-optional.txt hittades inte.%CLR_RESET%
    pause
    goto menu
)
echo.
echo %CLR_INFO%Installerar rekommenderade extras fraan requirements-optional.txt...%CLR_RESET%
%PYTHON_CMD% -m pip install -r requirements-optional.txt
echo.
pause
goto menu

:run_tests
call :set_python
echo.
echo %CLR_INFO%Koer tester...%CLR_RESET%
%PYTHON_CMD% -m pytest -q
echo.
pause
goto menu

:create_venv
call :set_python
if exist .venv (
    echo.
    echo .venv finns redan.
    pause
    goto menu
)
echo.
echo %CLR_INFO%Skapar .venv...%CLR_RESET%
%PYTHON_CMD% -m venv .venv
echo.
echo %CLR_OK%Klar.%CLR_RESET%
pause
goto menu

:activate_venv
if not exist .venv\Scripts\activate.bat (
    echo.
    echo Ingen .venv hittades. Vaelj alternativ 6 foerst.
    pause
    goto menu
)
echo.
echo %CLR_INFO%Oeppnar nytt skal med aktiv .venv...%CLR_RESET%
start "FINDUS>x<STRETCHING venv" cmd /k ".venv\Scripts\activate.bat"
goto menu

:python_repl
call :set_python
echo.
echo %CLR_INFO%Startar Python REPL...%CLR_RESET%
%PYTHON_CMD%
echo.
pause
goto menu

:compile_check
call :set_python
echo.
echo %CLR_INFO%Koer compileall-kontroll...%CLR_RESET%
%PYTHON_CMD% -m compileall app.py paulstretch_light tests
echo.
pause
goto menu

:build_exe
call :set_python
call :read_version
echo.
echo %CLR_INFO%Bygger Windows-paket via findus_stretching.spec...%CLR_RESET%
call :build_exe_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_OK%Bygget klart.%CLR_RESET%
echo Output:
echo   %cd%\dist\findus_stretching
echo.
pause
goto menu

:build_release_zip
call :set_python
call :read_version_silent
echo.
echo %CLR_INFO%Bygger releasepaket...%CLR_RESET%
call :build_exe_no_pause
if %errorlevel% neq 0 goto command_failed
call :create_release_zip_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_OK%Release-zip skapad.%CLR_RESET%
echo Output:
echo   %cd%\!ZIP_PATH!
echo.
pause
goto menu

:build_installer
call :set_python
call :read_version_silent
echo.
echo %CLR_INFO%Bygger Windows-installer...%CLR_RESET%
call :build_exe_no_pause
if %errorlevel% neq 0 goto command_failed
call :build_installer_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_OK%Installer klar.%CLR_RESET%
echo Output:
echo   %cd%\dist\installer
echo.
pause
goto menu

:full_release
call :set_python
call :read_version_silent
set "PREV_VERSION=!RELEASE_VERSION!"
echo.
echo %CLR_INFO%Koer full release med automatisk patch-bump...%CLR_RESET%
echo %CLR_INFO%Nuvarande version:%CLR_RESET% !PREV_VERSION!
echo.
echo %CLR_INFO%Steg 1/5: Bumpa patch-version...%CLR_RESET%
call :bump_patch_version_no_pause
if %errorlevel% neq 0 goto command_failed
echo %CLR_OK%Ny version:%CLR_RESET% !RELEASE_VERSION!
echo.
echo %CLR_INFO%Steg 2/6: Koer tester...%CLR_RESET%
%PYTHON_CMD% -m pytest -q
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_INFO%Steg 3/6: Bygger Windows-paket...%CLR_RESET%
call :build_exe_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_INFO%Steg 4/6: Bygger installer...%CLR_RESET%
call :build_installer_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_INFO%Steg 5/6: Skapar release-zip och latest-kopior...%CLR_RESET%
call :create_release_zip_no_pause
if %errorlevel% neq 0 goto command_failed
call :copy_latest_release_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_INFO%Steg 6/6: Skriver release-logg och changelog...%CLR_RESET%
call :write_release_log_no_pause
if %errorlevel% neq 0 goto command_failed
call :write_changelog_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_OK%Full release klar.%CLR_RESET%
call :stamp_now
echo Tid:
echo   !RELEASE_STAMP!
echo Version:
echo   !RELEASE_VERSION!
echo Artefakter:
echo   %cd%\dist\findus_stretching\findus_stretching.exe
echo   %cd%\dist\installer\findus_stretching_setup_v!RELEASE_VERSION!.exe
echo   %cd%\!ZIP_PATH!
echo   %cd%\dist\release\findus_stretching_setup_latest.exe
echo   %cd%\dist\release\findus_stretching_latest.zip
echo   %cd%\dist\release\release_log.txt
echo   %cd%\CHANGELOG_RELEASES.md
echo.
pause
goto menu

:minor_release
call :set_python
call :read_version_silent
set "PREV_VERSION=!RELEASE_VERSION!"
echo.
echo %CLR_INFO%Koer minor release med automatisk minor-bump...%CLR_RESET%
echo %CLR_INFO%Nuvarande version:%CLR_RESET% !PREV_VERSION!
echo.
echo %CLR_INFO%Steg 1/6: Bumpa minor-version...%CLR_RESET%
call :bump_minor_version_no_pause
if %errorlevel% neq 0 goto command_failed
echo %CLR_OK%Ny version:%CLR_RESET% !RELEASE_VERSION!
echo.
echo %CLR_INFO%Steg 2/6: Koer tester...%CLR_RESET%
%PYTHON_CMD% -m pytest -q
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_INFO%Steg 3/6: Bygger Windows-paket...%CLR_RESET%
call :build_exe_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_INFO%Steg 4/6: Bygger installer...%CLR_RESET%
call :build_installer_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_INFO%Steg 5/6: Skapar release-zip och latest-kopior...%CLR_RESET%
call :create_release_zip_no_pause
if %errorlevel% neq 0 goto command_failed
call :copy_latest_release_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_INFO%Steg 6/6: Skriver release-logg och changelog...%CLR_RESET%
call :write_release_log_no_pause
if %errorlevel% neq 0 goto command_failed
call :write_changelog_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_OK%Minor release klar.%CLR_RESET%
call :stamp_now
echo Tid:
echo   !RELEASE_STAMP!
echo Version:
echo   !RELEASE_VERSION!
echo Artefakter:
echo   %cd%\dist\findus_stretching\findus_stretching.exe
echo   %cd%\dist\installer\findus_stretching_setup_v!RELEASE_VERSION!.exe
echo   %cd%\!ZIP_PATH!
echo   %cd%\dist\release\findus_stretching_setup_latest.exe
echo   %cd%\dist\release\findus_stretching_latest.zip
echo   %cd%\dist\release\release_log.txt
echo   %cd%\CHANGELOG_RELEASES.md
echo.
pause
goto menu

:clean_artifacts
echo.
echo %CLR_INFO%Cleaning build artifacts...%CLR_RESET%
call :clean_artifacts_no_pause
if %errorlevel% neq 0 goto command_failed
echo.
echo %CLR_OK%build and dist removed.%CLR_RESET%
pause
goto menu

:show_menu_help
cls
echo %CLR_TITLE% ==================================================================== %CLR_RESET%
echo %CLR_TITLE%                           Option Guide                                %CLR_RESET%
echo %CLR_TITLE% ==================================================================== %CLR_RESET%
echo.
echo %CLR_MENU% [1] Start app %CLR_RESET%- Opens the app directly.
echo %CLR_MENU% [2] Quick start %CLR_RESET%- Installs base packages, runs tests, and starts the app.
echo %CLR_MENU% [3] Install dependencies %CLR_RESET%- Installs what is needed to develop and run the app.
echo %CLR_MENU% [4] Install recommended extras %CLR_RESET%- Installs extra tools for build and release tasks.
echo %CLR_MENU% [5] Run tests %CLR_RESET%- Checks that the project still works.
echo %CLR_MENU% [6] Create virtual environment %CLR_RESET%- Creates a separate Python environment for this project.
echo %CLR_MENU% [7] Open new shell with active .venv %CLR_RESET%- Opens a new command window with the correct environment already active.
echo %CLR_MENU% [8] Python REPL %CLR_RESET%- Opens a simple Python console for quick testing.
echo %CLR_MENU% [9] Compileall check %CLR_RESET%- Looks for obvious syntax errors in Python files.
echo %CLR_MENU% [10] Build Windows .exe %CLR_RESET%- Creates the runnable app folder in dist.
echo %CLR_MENU% [11] Create release zip %CLR_RESET%- Packs the built app into a zip file.
echo %CLR_MENU% [12] Build Setup.exe %CLR_RESET%- Creates a normal Windows installer.
echo %CLR_MENU% [13] Show installed packages %CLR_RESET%- Lists the installed Python packages.
echo %CLR_MENU% [14] Open project folder in Explorer %CLR_RESET%- Opens the project folder in Windows.
echo %CLR_MENU% [15] Open README %CLR_RESET%- Opens the project documentation.
echo %CLR_MENU% [16] Show recommended extras %CLR_RESET%- Explains the optional extra packages and why they are useful.
echo %CLR_MENU% [17] Full release %CLR_RESET%- Bumps the patch version and builds tests, exe, setup, zip, and logs.
echo %CLR_MENU% [18] Clean build artifacts %CLR_RESET%- Removes build and dist so you can rebuild from a clean state.
echo %CLR_MENU% [19] Minor release %CLR_RESET%- Bumps the middle version number and runs the full release chain.
echo %CLR_MENU% [20] Explain all options %CLR_RESET%- Shows this help page.
echo %CLR_MENU% [21] Write diagnostics report %CLR_RESET%- Creates diagnostics_report.txt that you can paste into chat.
echo %CLR_MENU% [22] Hard Reset %CLR_RESET%- Destroys .venv, caches, and builds to give you a clean slate.
echo %CLR_MENU% [23] Code Quality Check %CLR_RESET%- Runs Ruff to find unformatted code or missing variables.
echo.
echo %CLR_INFO%Versioning explained:%CLR_RESET%
echo   Patch release: 0.1.1 becomes 0.1.2. Good for small fixes and minor updates.
echo   Minor release: 0.1.1 becomes 0.2.0. Good when the app has gained clear new features.
echo.
echo %CLR_INFO%Recommendation:%CLR_RESET%
echo   Use [17] for normal new test releases.
echo   Use [19] when you feel you have added a bigger feature set.
echo.
pause
goto menu

:diagnostics_report
call :set_python
echo.
echo %CLR_INFO%Writing diagnostics report...%CLR_RESET%
%PYTHON_CMD% diagnostics.py
echo.
echo %CLR_OK%Open diagnostics_report.txt and paste it into chat if something breaks.%CLR_RESET%
pause
goto menu

:create_release_zip_no_pause
if not exist dist\release mkdir dist\release
set "ZIP_PATH=dist\release\findus_stretching_v!RELEASE_VERSION!.zip"
%PYTHON_CMD% tools\build_release_zip.py dist\findus_stretching "!ZIP_PATH!"
exit /b %errorlevel%

:build_exe_no_pause
%PYTHON_CMD% -m PyInstaller --version >nul 2>nul
if %errorlevel% neq 0 (
    echo %CLR_WARN%PyInstaller verkar inte vara installerat.%CLR_RESET%
    echo Installera extras med alternativ 4 eller koer:
    echo   %PYTHON_CMD% -m pip install -r requirements-optional.txt
    echo.
    exit /b 1
)
if not exist findus_stretching.spec (
    echo %CLR_WARN%findus_stretching.spec hittades inte.%CLR_RESET%
    echo Packaging-flodet foervaentar sig en projektstyrd spec-fil.
    echo.
    exit /b 1
)
%PYTHON_CMD% -m PyInstaller --noconfirm --clean findus_stretching.spec
exit /b %errorlevel%

:build_installer_no_pause
call :read_version_silent
set "ISCC_CMD=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "!ISCC_CMD!" (
    set "ISCC_CMD=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if not exist "!ISCC_CMD!" (
    set "ISCC_CMD=C:\Program Files\Inno Setup 6\ISCC.exe"
)
if not exist "!ISCC_CMD!" (
    echo %CLR_WARN%Inno Setup hittades inte.%CLR_RESET%
    echo Installera det med:
    echo   winget install --id JRSoftware.InnoSetup --exact
    echo.
    exit /b 1
)
if not exist findus_stretching_installer.iss (
    echo %CLR_WARN%findus_stretching_installer.iss hittades inte.%CLR_RESET%
    echo.
    exit /b 1
)
"!ISCC_CMD!" /Qp /DMyAppVersion=!RELEASE_VERSION! findus_stretching_installer.iss
exit /b %errorlevel%

:pip_list
call :set_python
echo.
echo %CLR_INFO%Visar installerade paket...%CLR_RESET%
%PYTHON_CMD% -m pip list
echo.
pause
goto menu

:open_explorer
echo.
echo %CLR_INFO%Oeppnar projektmappen...%CLR_RESET%
start "" explorer .
goto menu

:open_readme
echo.
echo %CLR_INFO%Oeppnar README i Notepad...%CLR_RESET%
start "" notepad README.md
goto menu

:show_optional_info
cls
echo %CLR_TITLE% =============================================================== %CLR_RESET%
echo %CLR_TITLE%                      Recommended Extras                        %CLR_RESET%
echo %CLR_TITLE% =============================================================== %CLR_RESET%
echo.
echo %CLR_MENU% pyqtgraph %CLR_RESET%- faster waveform rendering and future plotting upgrades
echo %CLR_MENU% pyinstaller %CLR_RESET%- build a Windows .exe for distribution
echo %CLR_MENU% sounddevice %CLR_RESET%- advanced Windows audio routing, host API selection, and non-default device control
echo.
echo %CLR_INFO%Install everything with:%CLR_RESET%
echo   %PYTHON_CMD% -m pip install -r requirements-optional.txt
echo.
pause
goto menu

:command_failed
echo.
echo %CLR_WARN%Ett kommando misslyckades. Kolla raden ovanfoer foer detaljer.%CLR_RESET%
pause
goto menu

:hard_reset
echo.
echo %CLR_WARN%VARNING: Detta tar bort .venv, __pycache__, build, och dist.%CLR_RESET%
set /p confirm=Aar du saeker? (j/n): 
if /I not "%confirm%"=="j" goto menu
echo.
echo %CLR_INFO%Rensar gamla byggfiler...%CLR_RESET%
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo %CLR_INFO%Rensar Python-cachar...%CLR_RESET%
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo %CLR_INFO%Rensar .venv...%CLR_RESET%
if exist .venv rmdir /s /q .venv
echo %CLR_OK%Allt aatarstaellt! Anvaend [2] Quick start eller [6] Create venv for att boerja om.%CLR_RESET%
pause
goto menu

:code_quality_check
call :set_python
echo.
echo %CLR_INFO%Koer Ruff linter (installerar ruff om det saknas)...%CLR_RESET%
%PYTHON_CMD% -m pip install ruff -q
%PYTHON_CMD% -m ruff check .
if %errorlevel% equ 0 (
    echo.
    echo %CLR_OK%Ruff hittade inga fel! Koden ser utmaerkt ut.%CLR_RESET%
) else (
    echo.
    echo %CLR_WARN%Ruff hittade varningar eller fel i koden. Se ovan.%CLR_RESET%
)
pause
goto menu

:start_pwa
call :set_python
echo.
echo %CLR_INFO%Startar lokal webbserver foer PWA...%CLR_RESET%
start cmd /k "cd web & %PYTHON_CMD% -m http.server 8000"
timeout /t 2 >nul
start http://localhost:8000
goto menu

