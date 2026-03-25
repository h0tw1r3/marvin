ARG PYTHON_VERSION=3.12
# true or false
ARG ENABLE_FIPS=false

FROM public.ecr.aws/amazonlinux/amazonlinux:2023 AS fips-false
ARG PYTHON_VERSION
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

WORKDIR /root

RUN --mount=type=cache,target=/var/cache/dnf <<EOD
echo "max_parallel_downloads=10" >> /etc/dnf/dnf.conf
echo "fastestmirror=True" >> /etc/dnf/dnf.conf
echo "install_weak_deps=False" >> /etc/dnf/dnf.conf
dnf install -y spal-release python${PYTHON_VERSION}-pip
EOD

RUN --mount=type=cache,target=/var/cache/dnf <<EOD
mkdir -p /sysroot/etc/dnf/vars
cp /etc/dnf/dnf.conf /sysroot/etc/dnf/dnf.conf
echo "releasever=$(rpm -q system-release --qf '%{VERSION}')" > /sysroot/etc/dnf/vars/releasever

dnf install -y \
  --releasever=$(rpm -q system-release --qf '%{VERSION}') \
  --installroot /sysroot \
  crypto-policies-scripts \
  spal-release
EOD

FROM fips-false AS fips-true
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

RUN chroot /sysroot update-crypto-policies --set FIPS

FROM fips-${ENABLE_FIPS} AS sysroot
ARG PYTHON_VERSION
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/cache/dnf <<EOD
dnf install -y \
  --releasever=$(rpm -q system-release --qf '%{VERSION}') \
  --installroot /sysroot \
    git \
    openssh-clients \
    ripgrep \
    python${PYTHON_VERSION}
EOD

WORKDIR /source
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    --mount=type=bind,source=./,target=/source <<EOD
python${PYTHON_VERSION} -m pip install --no-cache-dir --upgrade uv
uv export --no-hashes --no-header --no-annotate --no-install-project --no-dev --format requirements.txt > /tmp/requirements.txt
python${PYTHON_VERSION} -m pip install --root=/sysroot --no-cache-dir -r /tmp/requirements.txt
python${PYTHON_VERSION} -m pip install --root=/sysroot --no-cache-dir .
EOD

RUN <<EOD
dnf -y --installroot /sysroot remove crypto-policies-scripts
dnf -y --installroot /sysroot autoremove
dnf -y --installroot /sysroot clean all
rm -rf /sysroot/var/lib/dnf /sysroot/var/lib/rpm /sysroot/var/log/*
EOD

FROM scratch
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=sysroot /sysroot/ /

WORKDIR /app

RUN <<EOF
git config --global --add safe.directory '*'
git config --global core.quotepath false
EOF
