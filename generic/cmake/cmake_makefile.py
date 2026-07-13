import os
import shutil
import powermake
import typing as T
import powermake.package


parser = powermake.ArgumentParser()
parser.add_argument("--cmake-static", help="instruct cmake to prefer building a static lib if possible", action="store_true")
parser.add_argument("--dependency", metavar="DEPENDENCY", help="syntax: libname,min_ver,max_ver, may be given multiple time", action="append", default=[])
parser.add_argument("--cmake-flag", metavar="FLAG", help="A flag to transmit to CMake, may be given multiple time", action="append", default=[])
parser.add_argument("--autogen-sh", help="Run `bash autogen.sh` before anything else", action="store_true")
parser.add_argument("--remove-one-subfolder", metavar="folder_name", help="If the install had an unwanted subfolder, like lib/mariadb/mariadb.so, remove this subfolder to end up with lib/mariadb.so", default=None)


args_parsed = parser.parse_args()


def on_build(config: powermake.Config):
    if config._args_parsed.install is None:
        raise powermake.PowerMakeValueError("You should use this makefile with -r and --install")

    install_path = config._args_parsed.install

    dependencies = []

    powermake_libs_dir = os.path.abspath(os.path.join(install_path, "../../../../../"))

    if "ASM" in os.environ:
        del os.environ["ASM"]  # This might not have the same meaning for CMake

    if args_parsed.autogen_sh:
        if powermake.run_command(config, ["bash", "autogen.sh"], cwd="..") != 0:
            raise powermake.PowerMakeRuntimeError("autogen failed")


    for dep in args_parsed.dependency:
        force = ""
        count = dep.count(',')
        if count == 2:
            dep_name, dep_min_ver, dep_max_ver = dep.split(',')
        elif count == 3:
            dep_name, dep_min_ver, dep_max_ver, force = dep.split(',')
            if force != "force":
                raise powermake.PowerMakeValueError("dependency syntax: libname,min_ver,max_ver[,force]")
        else:
            raise powermake.PowerMakeValueError("dependency syntax: libname,min_ver,max_ver[,force]")

        if dep_min_ver == 'None':
            dep_min_ver = None
        if dep_max_ver == 'None':
            dep_max_ver = None

        lib = powermake.package.find_lib(config, dep_name, install_dir=powermake_libs_dir, min_version=dep_min_ver, max_version=dep_max_ver)

        if force == "force":
            args_parsed.cmake_flag.extend([
                f"-DCMAKE_C_STANDARD_LIBRARIES={lib.lib_file}",
                f"-DCMAKE_CXX_STANDARD_LIBRARIES={lib.lib_file}"
            ])

        dependencies.append(lib)

    print("dependencies found:", dependencies)

    powermake.run_cmake(config, "..", "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_INSTALL_PREFIX={install_path}", *args_parsed.cmake_flag, prefer_static=args_parsed.cmake_static, dependencies=dependencies)
    if powermake.run_command(config, ["cmake", "--build", ".", "--config", "Release", "-j", str(os.cpu_count() or 2)]) != 0:
        raise powermake.PowerMakeRuntimeError("build failed")

def on_install(config: powermake.Config, install_path: T.Union[str, None]):
    if install_path is None or not config.rebuild:
        raise powermake.PowerMakeValueError("You should use this makefile with -r and --install")
    if powermake.run_command(config, ["cmake", "--install", ".", "--prefix", install_path]) != 0:
        raise powermake.PowerMakeRuntimeError("cmake install failed")

    if args_parsed.remove_one_subfolder is not None:
        os.rename(os.path.join(install_path, "lib", args_parsed.remove_one_subfolder), os.path.join(install_path, "temp_lib"))
        shutil.rmtree(os.path.join(install_path, "lib"))
        os.rename(os.path.join(install_path, "temp_lib"), os.path.join(install_path, "lib"))

powermake.run("generic_cmake", build_callback=on_build, install_callback=on_install, args_parsed=args_parsed)
