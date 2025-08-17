# 编译 OpenCV

使用 bash 而不是 zsh 避免编译失败

下面是可以自行修改的变量，需要根据当前环境进行调整

```bash
project_dir=$HOME/project # source code directory(.tar.gz)
install_dir=$HOME/program # install directory
VERSION=4.12.0

clean_build_cache=true
use_ninja=false
enable_cuda=false
enable_cudnn=false
enable_onnxruntime=false
force_3rdparty_build=false
```

根据您提供的信息，您在安装OpenCV时遇到了一个关于GPU架构不支持的错误。这个问题可能是由于您的GPU架构与编译器内置的默认架构不兼容造成的。
为了解决这个问题，您可以尝试以下几个步骤：
确保您的GPU架构与OpenCV版本的要求相符。首先确定您的GPU型号，并查找其计算能力（Compute Capability）。可以在NVIDIA官方网站或其他资源上找到与您的GPU型号对应的计算能力。
在编译OpenCV之前，在CMake配置时指定GPU架构。打开CMake配置界面，找到CUDA相关的选项，并将CUDA_ARCH_BIN设置为与您的GPU计算能力相对应的架构。例如，如果您的计算能力为3.0（对应compute_30），则将该选项设置为"3.0"。
如果在使用CMake进行配置时未看到CUDA相关的选项，请确保您已正确安装了CUDA Toolkit，并配置了相应的环境变量。
完成CMake配置后，重新运行make命令以编译OpenCV。

set(CUDA_NVCC_FLAGS -gencode;arch=compute_30,code=sm_30;-gencode;arch=compute_35,code=sm_35;-gencode;arch=compute_37,code=sm_37;-gencode;arch=compute_50,code=sm_50;-gencode;arch=compute_52,code=sm_52;-gencode;arch=compute_60,code=sm_60;-gencode;arch=compute_61,code=sm_61;-gencode;arch=compute_70,code=sm_70;-gencode;arch=compute_75,code=sm_75;-D_FORCE_INLINES;-Xcompiler;-DCVAPI_EXPORTS;-Xcompiler;-fPIC;--std=c++11 ;; )

[CMake Error at cuda_compile_1_generated_gpu_mat.cu.o.RELEASE.cmake:222 (message): #25215](https://github.com/opencv/opencv/issues/25215)
