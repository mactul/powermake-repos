import os
import powermake
import typing as T
import powermake.package


parser = powermake.ArgumentParser()
parser.add_argument("--cmake-static", help="instruct cmake to prefer building a static lib if possible", action="store_true")
parser.add_argument("--dependency", metavar="DEPENDENCY", help="syntax: libname,min_ver,max_ver, may be given multiple time", action="append", default=[])
parser.add_argument("--cmake-flag", metavar="FLAG", help="A flag to transmit to CMake, may be given multiple time", action="append", default=[])

args_parsed = parser.parse_args()


def on_build(config: powermake.Config):
    if config._args_parsed.install is None:
        raise powermake.PowerMakeValueError("You should use this makefile with -r and --install")

    install_path = config._args_parsed.install

    dependencies = []

    powermake_libs_dir = os.path.abspath(os.path.join(install_path, "../../../../../"))


    for dep in args_parsed.dependency:
        if dep.count(',') != 2:
            raise powermake.PowerMakeValueError("dependency syntax: libname,min_ver,max_ver")
        dep_name, dep_min_ver, dep_max_ver = dep.split(',')
        if dep_min_ver == 'None':
            dep_min_ver = None
        if dep_max_ver == 'None':
            dep_max_ver = None

        dependencies.append(powermake.package.find_lib(config, dep_name, powermake_libs_dir, min_version=dep_min_ver, max_version=dep_max_ver))

    powermake.run_cmake(config, "..", "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_INSTALL_PREFIX={install_path}", *args_parsed.cmake_flag, prefer_static=args_parsed.cmake_static, dependencies=dependencies)
    if powermake.run_command(config, ["make", "-j8"]) != 0:
        raise powermake.PowerMakeRuntimeError("make failed")

def on_install(config: powermake.Config, install_path: T.Union[str, None]):
    if install_path is None or not config.rebuild:
        raise powermake.PowerMakeValueError("You should use this makefile with -r and --install")
    if powermake.run_command(config, ["cmake", "--install", ".", "--prefix", install_path]) != 0:
        raise powermake.PowerMakeRuntimeError("cmake install failed")

powermake.run("generic_cmake", build_callback=on_build, install_callback=on_install, args_parsed=args_parsed)
