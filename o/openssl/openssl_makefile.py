import os
import shutil
import powermake
import typing as T

def windows_refresh_path_from_registry() -> None:
    """Rebuild PATH from the registry (System + User), like a fresh shell would."""

    import winreg

    def read_env(root, subkey):
        try:
            with winreg.OpenKey(root, subkey) as key:
                value, _ = winreg.QueryValueEx(key, "Path")
                return value
        except FileNotFoundError:
            return ""

    system_path = read_env(
        winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    )
    user_path = read_env(winreg.HKEY_CURRENT_USER, r"Environment")

    os.environ["PATH"] = os.environ["PATH"] + ';' + system_path + ';' + user_path

def windows_get_perl(config: powermake.Config) -> str:
    PERL_DEFAULT_INSTALL_PATH = "C:\\Strawberry\\perl\\bin\\perl.exe"
    if os.path.exists(PERL_DEFAULT_INSTALL_PATH):
        return PERL_DEFAULT_INSTALL_PATH

    if powermake.run_command(config, ["winget", "install", "-e", "--id", "StrawberryPerl.StrawberryPerl"]) != 0:
        raise powermake.PowerMakeRuntimeError("Unable to install Strawberry Perl, required to compile OpenSSL")
    windows_refresh_path_from_registry()

    if os.path.exists(PERL_DEFAULT_INSTALL_PATH):
        return PERL_DEFAULT_INSTALL_PATH

    perl_exe = shutil.which("perl")

    if perl_exe is None:
        raise powermake.PowerMakeRuntimeError("Unable to find Strawberry Perl, required to compile OpenSSL")

    return perl_exe

def windows_get_nasm(config: powermake.Config) -> None:
    if shutil.which("nasm") is not None:
        return

    if powermake.run_command(config, ["winget", "install", "-e", "--id", "NASM.NASM"]) != 0:
        raise powermake.PowerMakeRuntimeError("Unable to install Nasm, required to compile OpenSSL")
    windows_refresh_path_from_registry()

    if shutil.which("nasm") is None:
        raise powermake.PowerMakeRuntimeError("Unable to find Strawberry Perl, required to compile OpenSSL")

def on_build(config: powermake.Config) -> None:
    if config._args_parsed.install is not None:
        install_path = config._args_parsed.install
    else:
        install_path = "./install"

    configure_args = [f"--prefix={install_path}", f"--openssldir={os.path.join(install_path, "ssl")}"]

    perl_exe = shutil.which("perl")

    if perl_exe is None:
        if config.host_is_windows():
            perl_exe = windows_get_perl(config)
        else:
            raise powermake.PowerMakeRuntimeError("Unable to find perl, required to compile OpenSSL")

    if config.host_is_windows():
        windows_get_nasm(config)
        os.environ["AS"] = shutil.which("nasm") or ""
        os.environ["ASM"] = shutil.which("nasm") or ""

    target = None
    if config.target_is_mingw() and config.target_simplified_architecture == "x86":
        target = "mingw"
    elif config.target_is_mingw() and config.target_simplified_architecture == "x64":
        target = "mingw64"
    elif config.target_is_linux() and config.target_simplified_architecture == "x86" and config.c_compiler is not None and config.c_compiler.type == "clang":
        target = "linux-x86-clang"
    elif config.target_is_linux() and config.target_simplified_architecture == "x86":
        target = "linux-x86"
    elif config.target_is_linux() and config.target_simplified_architecture == "x64" and config.c_compiler is not None and config.c_compiler.type == "clang":
        target = "linux-x86_64-clang"
    elif config.target_is_linux() and config.target_simplified_architecture == "x64":
        target = "linux-x86_64"
    elif config.target_is_linux() and config.target_simplified_architecture == "arm64":
        target = "linux-aarch64"
    elif config.c_compiler.type == "msvc":
        configure_args.append("no-makedepend")
        configure_args.append("enable-static-vcruntime")
        if config.target_simplified_architecture == "x86":
            target = "VC-WIN32"
        elif config.target_simplified_architecture == "x64":
            target = "VC-WIN64A"
        elif config.target_simplified_architecture == "arm64":
            target = "VC-WIN64-ARM"
    # otherwise it's too risky to guess, better stick with autodetection

    if target is not None:
        configure_args.append(target)

    if powermake.run_command(config, [perl_exe, "Configure", *configure_args]) != 0:
        raise powermake.PowerMakeRuntimeError("configure failed")

    if config.c_compiler.type == "msvc":
        if powermake.run_command(config, ["nmake"]) != 0:
            raise powermake.PowerMakeRuntimeError("build failed")
    else:
        if powermake.run_command(config, ["make", "-j8"]) != 0:
            raise powermake.PowerMakeRuntimeError("build failed")

def on_install(config: powermake.Config, install_path: T.Union[str, None]):
    if config.c_compiler.type == "msvc":
        if powermake.run_command(config, ["nmake", "install"]) != 0:
            raise powermake.PowerMakeRuntimeError("install failed")
    else:
        if powermake.run_command(config, ["make", "install"]) != 0:
            raise powermake.PowerMakeRuntimeError("install failed")

powermake.run("openssl", build_callback=on_build, install_callback=on_install)
