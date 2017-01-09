# The LattE Integrale distribution is now the upstream for 4ti2 as well.
# We record here the version of the bundled, yet upstream 4ti2 package.
%global ver4ti2 1.5

Name:           latte-integrale
Version:        1.5.3
Release:        2
Summary:        Lattice point enumeration

License:        GPLv2+
URL:            http://www.math.ucdavis.edu/~latte/software.php
Source0:        http://www.math.ucdavis.edu/~latte/software/%{name}-%{version}.tar.gz
Source1:        http://www.4ti2.de/4ti2_manual.pdf
# Adapt to changes in C++ lookup scope in GCC 4.7.  Sent upstream 8 Oct 2012.
Patch0:         4ti2-gcc47.patch
# Fix warnings that indicate possible runtime problems.
# Sent upstream 8 Oct 2012.
Patch1:         %{name}-warning.patch
# Upstream patch to fix an out-of-bounds array access in the Gaussian
# reduction code.
Patch2:         4ti2-gaussian.patch

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
Version:        %{ver4ti2}
Summary:        A software package for problems on linear spaces
Requires:       4ti2-libs%{?_isa} = %{ver4ti2}-%{release}
Requires:       latte-integrale

# This can be removed once Fedora 18 reaches EOL.
Provides:       4ti2 = %{version}-%{release}
Obsoletes:      4ti2 < 1.5-1

%description -n 4ti2
A software package for algebraic, geometric and combinatorial problems
on linear spaces.

%package -n 4ti2-devel
Version:        %{ver4ti2}
Summary:        Headers needed to develop software that uses 4ti2
Requires:       4ti2-libs%{?_isa} = %{ver4ti2}-%{release}
Requires:       gmp-devel%{?_isa}

%description -n 4ti2-devel
Headers and library files needed to develop software that uses 4ti2.

%package -n 4ti2-libs
Version:        %{ver4ti2}
Summary:        Library files for programs that use 4ti2

%description -n 4ti2-libs
Library files for programs that use 4ti2.

%prep
%setup -q
cp -p %{SOURCE1} .

# Don't use bundled software; also delete the unused LiDIA files
rm -f cddlib* glpk* gmp* lidia* ntl*

# Unpack 4ti2 and latte-integrale
tar xzf 4ti2-%{ver4ti2}.tar.gz
tar xzf latte-int-%{version}.tar.gz

# Patch 4ti2
cd 4ti2-%{ver4ti2}
%patch0
%patch2

# Fix an underlinked test
sed -i "s/^LIBS =.*/& -l4ti2common/" test/zsolve/api/Makefile.in

# Fix encodings
iconv -f ISO8859-1 -t UTF-8 NEWS > NEWS.utf8
touch -r NEWS NEWS.utf8
mv -f NEWS.utf8 NEWS

# Patch latte-integrale
cd ../latte-int-%{version}
%patch1

# Fix the cddlib search path, lrslib binary name
sed -e "s|cdd\.h|cddlib/cdd.h|" -e "s/lrs1/lrs/" -i configure

# Maybe fix the 4ti2 library search path
%ifarch x86_64
  sed -i "s|{FORTYTWO_HOME}/lib|&64|" configure
%endif

# Some tests fail because they timeout on slower processors.  Eliminate the
# timeouts and let koji kill us if a test infloops.
sed -i 's/ulimit -t $MAXRUNTIME; //' code/test-suite/test.pl.in

%build
# Build 4ti2 first
cd 4ti2-%{ver4ti2}
%configure2_5x --enable-shared --disable-static LIBS="-lgmpxx -lgmp" \
  CPPFLAGS="-D_GNU_SOURCE=1"

# Get rid of undesirable hardcoded rpaths; workaround libtool reordering
# -Wl,--as-needed after all the libraries; also fix a typo.
sed -e 's/func_apped/func_append/' \
    -e 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' \
    -e 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' \
    -e 's|^LTCC="gcc"|LTCC="gcc -Wl,--as-needed"|' \
    -e 's|^CC="g++"|CC="g++ -Wl,--as-needed"|' \
    -i libtool

make %{?_smp_mflags}

# Do a fake install of 4ti2 for building latte-integrale
mkdir ../local
make install DESTDIR=$PWD/../local

# Now build latte-integrale itself
cd ../latte-int-%{version}
%configure2_5x --enable-DATABASE --with-4ti2=$PWD/../local/%{_prefix} \
  CPPFLAGS="-I%{_includedir}/cddlib -D_GNU_SOURCE=1"
make %{?_smp_mflags}

%install
# Install 4ti2
cd 4ti2-%{ver4ti2}
%make_install
mkdir -p %{buildroot}%{_includedir}/tmp
mv %{buildroot}%{_includedir}/{4ti2,groebner,util,zsolve} \
   %{buildroot}%{_includedir}/tmp
mv %{buildroot}%{_includedir}/tmp %{buildroot}%{_includedir}/4ti2

# Install latte-integrale
cd ../latte-int-%{version}
%make_install

# Some binaries have too-generic names
for bin in count integrate triangulate; do
  mv %{buildroot}%{_bindir}/$bin %{buildroot}%{_bindir}/latte-$bin
done

# We don't need or want libtool files
rm -f %{buildroot}%{_libdir}/*.la

# We don't want documentation and examples in _datadir
mkdir -p %{buildroot}%{_docdir}
mv %{buildroot}%{_datadir}/latte-int %{buildroot}%{_docdir}/%{name}-%{version}

# Install missing documentation files
cp -p AUTHORS COPYING TODO %{buildroot}%{_docdir}/%{name}-%{version}

%check
export LD_LIBRARY_PATH=$PWD/local/%{_libdir}

# Check 4ti2
cd 4ti2-%{ver4ti2}
make check

# Check LattE
cd ../latte-int-%{version}
make check

%files
%{_docdir}/%{name}-%{version}/
%{_bindir}/*

%files -n 4ti2
%doc 4ti2_manual.pdf

%files -n 4ti2-devel
%{_includedir}/4ti2/
%{_libdir}/lib4ti2*.so
%{_libdir}/libzsolve*.so

%files -n 4ti2-libs
%doc 4ti2-%{ver4ti2}/COPYING 4ti2-%{ver4ti2}/NEWS
%doc 4ti2-%{ver4ti2}/README 4ti2-%{ver4ti2}/TODO
%{_libdir}/lib4ti2*.so.*
%{_libdir}/libzsolve*.so.*
