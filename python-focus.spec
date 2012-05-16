%global mod_name C4GD_web

Name:           python-focus
Version:        1.0
Release:        0%{?dist}
Summary:        Sample interface to OpenStack

Group:          Development/Libraries
License:        Apache 2.0
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools
Requires:       python-flask
Requires:       python-flask-wtf
Requires:       python-jinja2
Requires:       python-storm
Requires:       python-storm-mysql
Requires:       python-wtforms
Requires:       python-werkzeug
Requires:       python-hamlish-jinja
Requires:       python-requests
Requires:       python-gevent

%description


%prep
%setup -q 

%build
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

 
%files
%{python_sitelib}/*


%changelog
* Fri May 11 2012 Alessio Ababilov <aababilov@griddynamics.com> - 1.0-0
- Initial RPM release
