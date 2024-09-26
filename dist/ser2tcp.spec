#
# spec file for package ser2tcp
#

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#
%define name ser2tcp
%define version 0.0.0
%define release 0
%define setup_py setup.py
%define revision 3b641d7

%{?!python_module:%define python_module() python-%{**} python3-%{**}}
Name:           ser2tcp
Version:        0.0
Release:        0
Summary:        Common implementation for DB4SIL2 modules
License:        GPL-2.0-only
#Url:            https://github.com/vathe83/ser2tcp
Source0:        %{name}-%{revision}.tar
BuildRequires:  %{python_module setuptools}
Group:          Development/Tools/Other
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix:         %{_prefix}
BuildArch:      noarch
BuildRequires:  fdupes

%description
Common definitions for both server and client.
Mostly consists of attrs classes for information sent in messages.
Messages are simply attrs classes, which are serialised and deserialised over a
bidirectional asyncio stream by the Stream class.

%package        devel
Summary:        Development files for %{name}
Requires:       %{name} = %{version}

%description    devel
The %{name}-devel package contains modules for
developing DB4SIL2.

%prep
%setup -q -b 0 -n %{name}-%{revision}

%build
python3 %{setup_py} build

%install
python3 %{setup_py} install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
%python_expand %fdupes %{buildroot}%{$python_sitelib}

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/usr/lib

%files devel

%changelog