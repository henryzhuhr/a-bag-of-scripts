#!/bin/bash
set -e

# OpenCV Get Started: https://opencv.org/get-started
# Build from source
#   - Linux: https://docs.opencv.org/master/d7/d9f/tutorial_linux_install.html
#   - MacOS: https://docs.opencv.org/master/d0/db2/tutorial_macos_install.html


project_dir=$HOME/project # source code directory(.tar.gz)
install_dir=$HOME/program # install directory
VERSION=4.12.0

clean_build_cache=true
use_ninja=false
enable_cuda=false
enable_cudnn=false
enable_onnxruntime=false
force_3rdparty_build=false

start_time=$(date +%s)

# ========= log utils ==============
DEFAULT=$(echo -en '\033[0m')
LRED=$(echo -en '\033[01;31m')
LGREEN=$(echo -en '\033[01;32m')
LYELLOW=$(echo -en '\033[01;33m')
LBLUE=$(echo -en '\033[01;34m')
function log_base() { local emoji=$1 level=$2 color=$3 msg=$4; echo -e " ${emoji} ${color} $(date +"%Y-%m-%d %H:%M:%S") [${level}] $msg$DEFAULT"; }
function log_info()    { log_base "ℹ️" "INFO" "$LBLUE" "$1"; }
function log_success() { log_base "✅" "SUCCESS" "$LGREEN" "$1"; }
function log_warn()    { log_base "⚠️" "WARN" "$LYELLOW" "$1"; }
function log_error()   { log_base "❌" "ERROR" "$LRED" "$1"; exit 1; }
function log_fatal()   { log_base "❌" "FATAL" "$LRED" "$1"; exit 1; }

# ========= Directory Setup ===============
if [ ! -d "$project_dir" ]; then
    mkdir -p "$project_dir"
fi
cd "$project_dir" || exit

source_dir="$project_dir/opencv"
contrib_dir="$project_dir/opencv_contrib"
build_dir="/tmp/opencv-build"
install_prefix="$install_dir/opencv-$VERSION"


# ========= Git Clone & Checkout ==========

# # 检出 OpenCV 主仓库
# if [ ! -d "$source_dir" ]; then
#     git clone https://github.com/opencv/opencv.git  "$source_dir"
# fi

# if [ ! -d "$source_dir" ]; then
#     echo "error: opencv source not found in $source_dir"
#     exit 1
# fi

# cd "$source_dir" || exit 1

# # 先检查是否已经存在名为 $VERSION 的分支或标签
# if git rev-parse --verify $VERSION > /dev/null 2>&1; then
#     git checkout $VERSION
# else
#     git checkout tags/$VERSION -b $VERSION
# fi

# # 检出 OpenCV Contrib 仓库
# if [ ! -d "$contrib_dir" ]; then
#     git clone https://github.com/opencv/opencv_contrib.git  "$contrib_dir"
# fi

# if [ ! -d "$contrib_dir" ]; then
#     echo "error: opencv_contrib source not found in $contrib_dir"
#     exit 1
# fi

# cd "$contrib_dir" || exit 1

# # 同样的逻辑处理 contrib 仓库
# if git rev-parse --verify $VERSION > /dev/null 2>&1; then
#     git checkout $VERSION
# else
#     git checkout tags/$VERSION -b $VERSION
# fi

checkout_opencv_repo() {
    local repo_url="$1"
    local repo_dir="$2"
    local version="$3"

    if [ ! -d "$repo_dir" ]; then
        git clone "$repo_url" "$repo_dir"
    fi

    cd "$repo_dir" || exit 1

    # Check if branch or tag exists
    if git rev-parse --verify "$version" > /dev/null 2>&1; then
        git checkout "$version"
    else
        git checkout tags/"$version" -b "$version"
    fi
}

echo "Cloning and checking out OpenCV..."
checkout_opencv_repo "https://github.com/opencv/opencv.git " "$source_dir" "$VERSION"

echo "Cloning and checking out OpenCV Contrib..."
checkout_opencv_repo "https://github.com/opencv/opencv_contrib.git " "$contrib_dir" "$VERSION"

# ========= Opencv CMake Args ====================
additonal_args="\
-DWITH_AVIF=ON \
-DWITH_WAYLAND=ON \
-DWITH_VULKAN=ON \
-DWITH_OPENVINO=ON \
-DWITH_WEBNN=ON \
-DBUILD_TIFF=ON \
-DWITH_JPEGXL=ON \
-DWITH_OPENEXR=ON \
-DWITH_OPENGL=ON \
-DWITH_OPENVX=ON \
-DWITH_OPENNI=ON \
-DWITH_OPENNI2=ON \
-DWITH_SPNG=ON \
-DWITH_GDCM=ON \
-DWITH_PVAPI=ON \
-DWITH_ARAVIS=ON \
-DWITH_QT=ON \
-DWITH_TBB=ON \
-DWITH_HPX=ON \
-DWITH_OPENMP=ON \
-DWITH_MSMF_DXVA=ON \
-DWITH_XIMEA=ON \
-DWITH_UEYE=ON \
-DWITH_XINE=ON \
-DWITH_CLP=ON \
-DWITH_OPENCL=ON \
-DWITH_OPENCL_SVM=ON \
-DWITH_LIBREALSENSE=ON \
-DWITH_MFX=ON \
-DWITH_GDAL=ON \
-DWITH_GPHOTO2=ON \
-DWITH_QUIRC=ON \
-DWITH_TIMVX=ON \
-DWITH_CANN=ON \
-DWITH_ZLIB_NG=ON \
"

# ENABLE_CCACHE


if [ "$force_3rdparty_build" = "true" ]; then
    additonal_args+=" -DOPENCV_FORCE_3RDPARTY_BUILD=ON"
fi

# ========= Python Setup ==================
PYTHON3_EXECUTABLE=$(which python3)
PYTHON3_LDLIBRARY=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LDLIBRARY'))")
PYTHON3_INCLUDE_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('INCLUDEPY'))")
PYTHON3_NUMPY_INCLUDE_DIRS=$(python3 -c "import numpy; print(numpy.get_include())")

if [ -z "$PYTHON3_NUMPY_INCLUDE_DIRS" ]; then
    log_fatal "numpy not found. Please install it first: python3 -m pip install numpy"
fi

PYTHON3_ARGS="-DPYTHON3_EXECUTABLE=$PYTHON3_EXECUTABLE -DPYTHON3_INCLUDE_DIR=$PYTHON3_INCLUDE_DIR -DPYTHON3_NUMPY_INCLUDE_DIRS=$PYTHON3_NUMPY_INCLUDE_DIRS"
PYTHON3_ARGS+=" -DBUILD_opencv_python2=OFF -DBUILD_opencv_python3=ON -DBUILD_opencv_python_bindings_generator=ON"
log_info "Python3 arguments: $PYTHON3_ARGS"
additonal_args+=" $PYTHON3_ARGS"

# ========= Opencv CMake Args: CUDA Support ================

if [ $enable_cuda = "true" ]; then
    GPU_ARCH=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | awk '{print $1}' | head -n1 | tr '.' ' ')
    CUDA_ARCH_BIN=$(echo "$GPU_ARCH" | awk '{printf "%.1f", $1 + 0.0}')

    log_info "Detected GPU architecture: $GPU_ARCH"
    log_info "Setting CUDA_ARCH_BIN to: $CUDA_ARCH_BIN"

    CUDA_ARGS="-DWITH_CUDA=ON -DOPENCV_DNN_CUDA=ON"
    # https://github.com/opencv/opencv/issues/25215
    # depends on -DBUILD_TIFF=ON in jetson
    # -DCUDA_ARCH_BIN=8.7 can be auto set by -DCUDA_GENERATION=Auto
    # -DCUDA_ARCH_BIN=${CUDA_ARCH_BIN} -DCUDA_ARCH_PTX=${CUDA_ARCH_BIN}
    CUDA_ARGS="-DWITH_CUDA=ON -DCUDA_ARCH_BIN=${CUDA_ARCH_BIN} -DCUDA_ARCH_PTX=${CUDA_ARCH_BIN} -DOPENCV_DNN_CUDA=ON -DCMAKE_CUDA_COMPILER=${CUDA_HOME}/bin/nvcc"
    # CUDA_ARGS="-DWITH_CUDA=ON -DCUDA_GENERATION=Auto -DOPENCV_DNN_CUDA=ON -DCMAKE_CUDA_COMPILER=${CUDA_HOME}/bin/nvcc"

    additonal_args+=" $CUDA_ARGS"
    
    # err:
    #     error: ambiguous overload for ‘operator!=’ (operand types are ‘__half’ and ‘double’)
    #     114 |             if (weight != 1.0)
    # fix in: https://github.com/opencv/opencv/pull/24104/
    #   use version later than ab8cb6f8a9034da2a289b84685c6d959266029be
    # 
    # https://github.com/Qengineering/Install-OpenCV-Jetson-Nano/issues/27
    # 
    #
    # CMake Warning at /home/jetson/project/opencv_contrib/modules/cudacodec/CMakeLists.txt:26 (message):
    # cudacodec::VideoReader requires Nvidia Video Codec SDK.  Please resolve
    # dependency or disable WITH_NVCUVID=OFF
    #
    # CMake Warning at /home/jetson/project/opencv_contrib/modules/cudacodec/CMakeLists.txt:30 (message):
    # cudacodec::VideoWriter requires Nvidia Video Codec SDK.  Please resolve
    # dependency or disable WITH_NVCUVENC=OFF
    # 
fi

if [ "$enable_cudnn" = "true" ] && [ "$enable_cuda" = "true" ]; then
    additonal_args+=" -DWITH_CUDNN=ON"
fi

if [ $enable_onnxruntime = "true" ]; then
    if [ ! -z "$ORT_INSTALL_DIR" ]; then
        additonal_args+=" -DWITH_ONNX=ON -DONNXRT_ROOT_DIR=$ORT_INSTALL_DIR"
    else
        log_fatal "onnxruntime not found, please set variable \"ORT_INSTALL_DIR\""
    fi
fi

check_duplicate_cmake_args() {
    local ARGS="${1:-}"
    local formatted_args
    local duplicate_keys=()

    # 检查输入是否为空
    if [ -z "$ARGS" ]; then
        log_warn "No CMake arguments provided to check for duplicates."
        return 0
    fi

    # 格式化为每行一个参数，并过滤出 -Dxxx 类型
    formatted_args=$(echo "$ARGS" | tr ' ' '\n' | grep -E '^[-]D[^=]+')

    # 使用 awk 分析重复项并输出重复 key 到数组
    while IFS= read -r line; do
        duplicate_keys+=("$line")
    done < <(
        echo "$formatted_args" | awk -F= '
        $0 ~ /^-D/ {
            key = $1
            count[key]++
        }
        count[key] == 2 {
            print key
        }'
    )

    # 判断是否有重复项
    if [ ${#duplicate_keys[@]} -gt 0 ]; then
        duplicate_key_str=""
        for key in "${duplicate_keys[@]}"; do { duplicate_key_str+="$key "; } done
        log_fatal "found duplicate CMake arguments: $duplicate_key_str"
    fi
}

check_duplicate_cmake_args "$additonal_args"

log_info "OpenCV build additional args: $additonal_args"

# ========= Build Setup ===================
mkdir -p "$build_dir"
cd "$build_dir" || exit

if [ -f CMakeCache.txt ]; then
    echo "Removing old CMakeCache.txt..."
    rm -f CMakeCache.txt
fi

# ========= CMake Configure ==============
if ! command -v ninja &> /dev/null; then
    log_fatal "Command 'ninja' not found. Please install Ninja build system: 'apt install -y ninja-build'"
fi

# https://docs.opencv.org/4.x/d6/dea/tutorial_env_reference.html
GENERATOR=""
if [ "$use_ninja" = true ]; then
    GENERATOR="-G Ninja"
fi

# -DOPENCV_DOWNLOAD_MIRROR_ID=gitcode \
cmake "$GENERATOR" \
    -DCMAKE_INSTALL_PREFIX="$install_prefix" \
    -DOPENCV_EXTRA_MODULES_PATH="$contrib_dir/modules" \
    -DCMAKE_BUILD_TYPE=Release \
    -DOPENCV_GENERATE_PKGCONFIG=ON \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_STATIC_LIBS=ON \
    -DBUILD_PACKAGE=ON \
    -DBUILD_opencv_apps=ON \
    -DBUILD_EXAMPLES=OFF \
    -DPYTHON_DEFAULT_EXECUTABLE="$(which python3)" "$PYTHON3_ARGS" \
    "$additonal_args" \
    "$source_dir"

if [ $? -ne 0 ]; then
    log_fatal "CMake configuration failed, please check the output for errors."
fi

# ========= CPU Core Detection ============
if [ "$(uname)" = "Darwin" ]; then
    NUM_CORES=$(sysctl -n hw.ncpu)
    # For M1/M2 Macs, use specific optimization flags
    if [[ "$(uname -m)" == "arm64" ]]; then
        export CXXFLAGS="-DFORCE_ARM64 -mcpu=native"
    fi
elif [ "$(expr substr $(uname -s) 1 5)" = "Linux" ]; then
    NUM_CORES=$(nproc --all)
else
    NUM_CORES=1
fi

# ========= Build & Install ===============
if [ "$use_ninja" = true ]; then
    ninja -j"${NUM_CORES}" && ninja install
else
    make -j"${NUM_CORES}" && make install
fi

if [ $? -ne 0 ]; then
    log_fatal "Build failed, please check the output for errors."
fi

# ========= Cleanup Build Dir =============
if [ "$clean_build_cache" = "true" ]; then
    rm -rf "$build_dir"
fi

# ========= Set Env Variables =============
if ! grep -q "OpenCV_HOME" ~/.bashrc; then
    cat << EOF >> ~/.bashrc

# OpenCV environment variables
export OpenCV_HOME=${install_prefix}
export OpenCV_DIR=\$OpenCV_HOME/lib/cmake
export PATH=\$OpenCV_HOME/bin:\$PATH
export LD_LIBRARY_PATH=\$OpenCV_HOME/lib:\$LD_LIBRARY_PATH
EOF
    echo "[INFO] OpenCV environment variables added to ~/.bashrc"
else
    echo "[INFO] OpenCV environment variables already exist in ~/.bashrc"
fi

# ========= Create Symlink ================
if [ -L "$install_dir/opencv" ]; then
    rm -f "$install_dir/opencv"
fi
ln -s "$install_prefix" "$install_dir/opencv"


# ========= Final Output ==================
end_time=$(date +%s)
duration=$((end_time - start_time))
log_success "✅ Build completed successfully!"
echo "
    🕒 Total time: ${duration} seconds
    📌 Installed at: $install_prefix
    🔗 Symlinked to: $install_dir/opencv
"

