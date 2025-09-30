#!/bin/bash
set -e

echoca () {
    case $1 in
        "red") tput setaf 1;;
        "green") tput setaf 2;;
        "orange") tput setaf 3;;
        "blue") tput setaf 4;;
        "purple") tput setaf 5;;
        "cyan") tput setaf 6;;
        "gray" | "grey") tput setaf 7;;
        "white") tput setaf 8;;
    esac
    echo "$2";
    tput sgr0
}

version="0.36.0"
os=$OSTYPE
arch=$(uname -m)
platform=""

echoca blue "Operating system: $os"
echoca blue "Architecture: $arch"

if [[ "$os" == "linux-gnu"* ]]; then
    if [[ "$arch" == "x86_64" ]]; then
        platform="linux64"
    elif [[ "$arch" == "aarch64" ]]; then
        platform="linux-aarch64"
    else
        echoca red "Unsupported architecture: $arch"
        exit 1
    fi
elif [[ "$os" == "darwin"* ]]; then
    if [[ "$arch" == "x86_64" ]]; then
        platform="macos"
    elif [[ "$arch" == "arm64" ]]; then
        platform="macos-aarch64"
    else
        echoca red "Unsupported architecture: $arch"
        exit 1
    fi
elif [[ "$os" == "msys"* ]]; then
    if [[ "$arch" == "x86_64" ]]; then
        platform="win64"
    elif [[ "$arch" == "aarch64" ]]; then
        platform="win-aarch64"
    else
        echoca red "Unsupported architecture: $arch"
        exit 1
    fi
else
    echoca red "Unsupported operating system: $os"
    exit 1
fi

echoca blue "Platform: $platform"

tarball_file="geckodriver-v${version}-${platform}.tar.gz"
sign_file="geckodriver-v${version}-${platform}.tar.gz.asc"

tarball_url="https://github.com/mozilla/geckodriver/releases/download/v${version}/${tarball_file}"
sign_url="https://github.com/mozilla/geckodriver/releases/download/v${version}/${sign_file}"

gecko_dir="webdrivers/gecko"
mkdir -p ${gecko_dir}

tarball_local_path=${gecko_dir}/${tarball_file}
sign_local_path=${gecko_dir}/${sign_file}

if [[ -f ${tarball_local_path} ]]; then
    echoca blue "Gecko tarball already exists at ${tarball_local_path}"
else
    echoca blue "Downloading Gecko tarball from ${tarball_url}"
    wget -P ${gecko_dir} ${tarball_url}
fi

# only linux has signature file
if [[ "$os" == "linux-gnu"* ]]; then
    echoca blue "Verifying signature from ${sign_url}"
    wget -P ${gecko_dir} ${sign_url}
    gpg --verify ${sign_local_path} ${tarball_local_path}

    if [[ $? -eq 0 ]]; then
        echoca green "Signature verified successfully"
    else
        echoca red "Signature verification failed"
        exit 1
    fi
fi

echoca blue "Extracting Gecko tarball to ${gecko_dir}"
tar -zxvf ${tarball_local_path} -C ${gecko_dir}

echoca green "Installation finished"

echoca red "Please add this line to your .bashrc or .zshrc file:"
echoca red "export PATH=\$PATH:$(pwd)/${gecko_dir}"

echoca green "Enjoy your Gecko!"
