from distutils.core import setup, Extension

setup(
    name = "quicklz",
    version = "1.0",
    ext_modules = [
        Extension(
            "quicklz",
            ["quicklz.c", "quicklzpy.c"],
            extra_compile_args=["-O2", "-march=native", "-DFORTIFY_SOURCE=2", "-fstack-protector"]
#            extra_compile_args=["-O2", "-march=native"]
#            extra_compile_args=["-O2", "-march=native", "-floop-interchange", "-floop-block", "-floop-strip-mine", "-ftree-loop-distribution"]
        )
    ]
)
