%global fortiver 1.6.7
%global lattever 1.7.3

%define _disable_lto 1
%define _disable_ld_no_undefined 1
%define _disable_rebuild_configure 1

Name:           latte-integrale
Version:        %{lattever}b
Release:        1
Summary:        Lattice point enumeration
Group:		Sciences/Mathematics
License:        GPLv2+
URL:            https://www.math.ucdavis.edu/~latte/software.php
Source0:        https://www.math.ucdavis.edu/~latte/software/packages/latte_current/%{name}-%{version}.tar.gz
Source1:        4ti2.module.in
Source2:	%{name}.rpmlintrc
# Fix warnings that indicate possible runtime problems.
Patch0:         %{name}-warning.patch
Patch1:		lidia-warning.patch

BuildRequires:  cdd
BuildRequires:  cddlib-devel
BuildRequires:  glpk-devel
BuildRequires:  gmpxx-devel
BuildRequires:  lrslib
BuildRequires:  ntl-devel
BuildRequires:  sqlite-devel
BuildRequires:  TOPCOM

Requires:       cdd
Requires:       TOPCOM

%description
LattE (Lattice point Enumeration) is a computer software dedicated to
the problems of counting lattice points and integration inside convex
polytopes.  LattE contains the first ever implementation of Barvinok's
algorithm.  The LattE macchiato version (by M. Köppe) incorporated
fundamental improvements and speed ups.  Now the latest version, LattE
integrale, has the ability to directly compute integrals of polynomial
functions over polytopes and in particular to do volume computations.

%package -n 4ti2
Version:        %{fortiver}
Summary:        A software package for problems on linear spaces
Requires:       4ti2-libs%{?_isa} = %{version}-%{release}
Requires:       latte-integrale
Requires:       environment-modules

%description -n 4ti2
A software package for algebraic, geometric and combinatorial problems
on linear spaces.

This package uses Environment Modules, to load the binaries onto
your PATH you will need to run module load 4ti2-%{_arch}

%package -n 4ti2-devel
Version:        %{fortiver}
Summary:        Headers needed to develop software that uses 4ti2
Requires:       4ti2-libs%{?_isa} = %{version}-%{release}
Requires:       gmp-devel%{?_isa}

%description -n 4ti2-devel
Headers and library files needed to develop software that uses 4ti2.

%package -n 4ti2-libs
Version:        %{fortiver}
Summary:        Library files for programs that use 4ti2

%description -n 4ti2-libs
Library files for programs that use 4ti2.

%prep
%setup -q

# Don't use bundled software
rm -f cddlib* glpk* gmp* ntl*

# Unpack 4ti2 and latte-integrale
tar xzf 4ti2-%{fortiver}.tar.gz
tar xzf lidia-base-2.3.0+latte-patches-2014-10-04.tar.gz
tar xzf lidia-FF-2.3.0+latte-patches-2014-10-04.tar.gz
tar xzf lidia-LA-2.3.0+latte-patches-2014-10-04.tar.gz
tar xzf latte-int-%{lattever}.tar.gz

# Fix encodings
cd 4ti2-%{fortiver}
iconv -f ISO8859-1 -t UTF-8 NEWS > NEWS.utf8
touch -r NEWS NEWS.utf8
mv -f NEWS.utf8 NEWS

# Patch latte-integrale
cd ../latte-int-%{lattever}
%patch0

# Fix the cddlib search path, lrslib binary name
sed -e "s|cdd\.h|cddlib/cdd.h|" -e "s/lrs1/lrs/" -i configure

# Maybe fix the 4ti2 library search path
%ifarch x86_64
  sed -i "s|{FORTYTWO_HOME}/lib|&64|" configure
%endif

# Some tests fail because they timeout on slower processors.  Eliminate the
# timeouts and let koji kill us if a test infloops.
sed -i 's/ulimit -t $MAXRUNTIME; //' code/test-suite/test.pl.in

# Patch lidia
cd ../lidia-2.3.0+latte-patches-2014-10-04
%patch1

%build
export CC=gcc
export CXX=g++
# Build 4ti2 first
cd 4ti2-%{fortiver}
%configure2_5x --enable-shared --disable-static LIBS="-lgmpxx -lgmp" \
  CPPFLAGS="-D_GNU_SOURCE=1"

# Get rid of undesirable hardcoded rpaths; workaround libtool reordering
# -Wl,--as-needed after all the libraries; also fix a typo.
sed -e 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' \
    -e 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' \
    -e 's|^LTCC="gcc"|LTCC="gcc -Wl,--as-needed"|' \
    -e 's|^CC="g++"|CC="g++ -Wl,--as-needed"|' \
    -i libtool

make %{?_smp_mflags}

# Do a fake install of 4ti2 for building latte-integrale
mkdir ../local
make install DESTDIR=$PWD/../local

# Next build LiDia
ln -s lidia ../local%{_includedir}/LiDIA
cd ../lidia-2.3.0+latte-patches-2014-10-04
cp -p ../{config.guess,config.sub,install-sh,ltmain.sh,missing} .
%configure2_5x --disable-nf --disable-ec --disable-eco --disable-gec \
  CFLAGS="%{optflags} -fPIC -fno-strict-aliasing" \
  CXXFLAGS="%{optflags} -fPIC -fno-strict-aliasing"
sed -i 's/-m64/& -fPIC -fno-strict-aliasing/' libtool library/Makefile \
  library/base/Makefile library/linear_algebra/Makefile \
  library/finite_fields/Makefile
make %{?_smp_mflags}

# Do a fake install of LiDia for building latte-integrale
make install DESTDIR=$PWD/../local
sed -i "s,%{_libdir},$PWD/../local&," ../local%{_libdir}/*.la

# Now build latte-integrale itself
cd ../latte-int-%{lattever}
sed -i 's|\(^LIBS = .*\)|\1 ../../latte/liblatte.la|' \
    code/latte/normalize/Makefile.in
%configure2_5x --enable-shared --disable-static \
  --enable-DATABASE --with-4ti2=$PWD/../local/%{_prefix} \
  CPPFLAGS="-I%{_includedir}/cddlib -D_GNU_SOURCE=1 -DNTL_STD_CXX" \
  LDFLAGS="-L$PWD/../local%{_libdir} $RPM_LD_FLAGS"

# Get rid of undesirable hardcoded rpaths; workaround libtool reordering
# -Wl,--as-needed after all the libraries.
sed -e 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' \
    -e 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' \
    -e 's|^LTCC="gcc"|LTCC="gcc -Wl,--as-needed"|' \
    -e 's|^CC="g++"|CC="g++ -Wl,--as-needed"|' \
    -i libtool

make %{?_smp_mflags}

%install
# Install 4ti2
cd 4ti2-%{fortiver}
%make_install
mkdir -p %{buildroot}%{_includedir}/tmp
mv %{buildroot}%{_includedir}/{4ti2,groebner,util,zsolve} \
   %{buildroot}%{_includedir}/tmp
mv %{buildroot}%{_includedir}/tmp %{buildroot}%{_includedir}/4ti2

# Move the 4ti2 binaries
mkdir -p %{buildroot}%{_libdir}/4ti2
mv %{buildroot}%{_bindir} %{buildroot}%{_libdir}/4ti2

# Make the environment-modules file
mkdir -p %{buildroot}%{_datadir}/Modules/modulefiles/
# Since we're doing our own substitution here, use our own definitions.
sed 's#@LIBDIR@#'%{_libdir}/4ti2'#g;' < %SOURCE1 >%{buildroot}%{_datadir}/Modules/modulefiles/4ti2-%{_arch}

# Install latte-integrale
cd ../latte-int-%{lattever}
%make_install

# Some binaries have too-generic names
for bin in count integrate triangulate; do
  mv %{buildroot}%{_bindir}/$bin %{buildroot}%{_bindir}/latte-$bin
done

# We don't need or want libtool files
rm -f %{buildroot}%{_libdir}/*.la

# Internal libraries only; don't install the .so since there are no headers
rm -f %{buildroot}%{_libdir}/lib{latte,normalize}.so

# We don't want documentation and examples in _datadir
mkdir -p %{buildroot}%{_docdir}
mv %{buildroot}%{_datadir}/4ti2 %{buildroot}%{_docdir}
mv %{buildroot}%{_datadir}/latte-int _docs_staging

# Install missing documentation files
cp -p AUTHORS COPYING TODO _docs_staging

%check
export LD_LIBRARY_PATH=$PWD/local/%{_libdir}:$PWD/latte-int-%{lattever}/code/latte/.libs

# Check 4ti2
cd 4ti2-%{fortiver}
make check

# Check LattE
cd ../latte-int-%{lattever}
make check

%files
%doc latte-int-%{lattever}/_docs_staging/*
%{_bindir}/*
%{_libdir}/liblatte.so.*
%{_libdir}/libnormalize.so.*

%files -n 4ti2
%{_docdir}/4ti2/
%{_libdir}/4ti2/
%{_datadir}/Modules/modulefiles/4ti2-%{_arch}

%files -n 4ti2-devel
%{_includedir}/4ti2/
%{_libdir}/lib4ti2*.so
%{_libdir}/libzsolve*.so

%files -n 4ti2-libs
%doc 4ti2-%{fortiver}/COPYING 4ti2-%{fortiver}/NEWS
%doc 4ti2-%{fortiver}/README 4ti2-%{fortiver}/TODO
%{_libdir}/lib4ti2*.so.*
%{_libdir}/libzsolve*.so.*
