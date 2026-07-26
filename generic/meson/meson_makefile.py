import os
import powermake
import typing as T
import powermake.package


parser = powermake.ArgumentParser()
parser.add_argument("--dependency", metavar="DEPENDENCY", help="syntax: libname,min_ver,max_ver[,force] ; may be given multiple time", action="append", default=[])
parser.add_argument("--meson-flag", metavar="FLAG", help="A flag to transmit to Meson, may be given multiple time", action="append", default=[])


args_parsed = parser.parse_args()


def on_build(config: powermake.Config):
    if config._args_parsed.install is None:
        raise powermake.PowerMakeValueError("You should use this makefile with -r and --install")

    install_path = config._args_parsed.install

    dependencies = []

    powermake_libs_dir = os.path.abspath(os.path.join(install_path, "../../../../../"))

    if "ASM" in os.environ:
        del os.environ["ASM"]  # This might not have the same meaning for Meson

    if "AR" in os.environ:
        del os.environ["AR"]  # On MSVC this might cause issues for Meson

    for dep in args_parsed.dependency:
        count = dep.count(',')
        if count == 2:
            dep_name, dep_min_ver, dep_max_ver = dep.split(',')
        else:
            raise powermake.PowerMakeValueError("dependency syntax: libname,min_ver,max_ver")

        if dep_min_ver == 'None':
            dep_min_ver = None
        if dep_max_ver == 'None':
            dep_max_ver = None

        lib = powermake.package.find_lib(config, dep_name, install_dir=powermake_libs_dir, min_version=dep_min_ver, max_version=dep_max_ver)

        dependencies.append(lib)

    print("dependencies found:", dependencies)

    powermake.run_meson(config, "build", "--buildtype=release", f"--prefix={install_path}", *args_parsed.meson_flag, dependencies=dependencies)
    if powermake.run_command(config, ["meson", "compile", "-C", "build"]) != 0:
        raise powermake.PowerMakeRuntimeError("build failed")

def on_install(config: powermake.Config, install_path: T.Union[str, None]):
    if powermake.run_command(config, ["meson", "install", "-C", "build"]) != 0:
        raise powermake.PowerMakeRuntimeError("meson install failed")

powermake.run("generic_meson", build_callback=on_build, install_callback=on_install, args_parsed=args_parsed)
