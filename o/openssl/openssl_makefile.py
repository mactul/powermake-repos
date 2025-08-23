import os
import powermake
import typing as T

def on_build(config: powermake.Config):
    if config._args_parsed.install is not None:
        install_path = config._args_parsed.install
    else:
        install_path = "./install"

    configure_args = [f"--prefix={install_path}", f"--openssldir={os.path.join(install_path, "ssl")}"]

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
    # otherwise it's to risky to guess, better stick with autodetection

    if target is not None:
        configure_args.append(target)

    if powermake.run_command(config, ["perl", "Configure", *configure_args]) != 0:
        raise powermake.PowerMakeRuntimeError("configure failed")
    if powermake.run_command(config, ["make", "-j8"]) != 0:
        raise powermake.PowerMakeRuntimeError("make failed")

def on_install(config: powermake.Config, install_path: T.Union[str, None]):
    if powermake.run_command(config, ["make", "install"]) != 0:
        raise powermake.PowerMakeRuntimeError("make install failed")

powermake.run("openssl", build_callback=on_build, install_callback=on_install)
