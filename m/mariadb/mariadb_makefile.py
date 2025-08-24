import os
import shutil
import powermake
import typing as T

def on_build(config: powermake.Config):
    if config._args_parsed.install is not None:
        install_path = config._args_parsed.install
    else:
        install_path = "./install"

    powermake.run_cmake(config, "..", "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_INSTALL_PREFIX={install_path}")
    if powermake.run_command(config, ["make", "-j8"]) != 0:
        raise powermake.PowerMakeRuntimeError("make failed")

def on_install(config: powermake.Config, install_path: T.Union[str, None]):
    if install_path is None:
        install_path = "./install"
    if powermake.run_command(config, ["cmake", "--install", ".", "--prefix", install_path]) != 0:
        raise powermake.PowerMakeRuntimeError("cmake install failed")
    os.rename(os.path.join(install_path, "lib", "mariadb"), os.path.join(install_path, "temp_lib"))
    shutil.rmtree(os.path.join(install_path, "lib"))
    os.rename(os.path.join(install_path, "temp_lib"), os.path.join(install_path, "lib"))

powermake.run("mariadb", build_callback=on_build, install_callback=on_install)
