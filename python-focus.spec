%global mod_name focus

Name:           python-focus
Version:        1.0
Release:        0%{?dist}
Summary:        Sample interface to OpenStack

Group:          Development/Libraries
License:        GNU LGPL 2.1
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools

Requires:       python-ldap
Requires:       python-flask >= 0.9
Requires:       python-flask-wtf == 0.6
Requires:       python-flask-principal
Requires:       python-flask-uploads
Requires:       python-flask-mail
Requires:       MySQL-python
Requires:       python-wtforms
Requires:       python-hamlish-jinja
Requires:       python-storm
Requires:       python-storm-mysql
Requires:       python-gunicorn
Requires:       python-memcached
Requires:       python-netaddr

Requires:       start-stop-daemon

Requires:       python-novaclient
Requires:       python-keystoneclient
Requires:       python-glanceclient
Requires:       python-openstackclient-base

Requires:       nginx-upload
Requires:       rrdtool-python


%description


%prep
%setup -q 


%build
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build


%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
rm -rf %{buildroot}%{python_sitelib}/*/tests

cd redhat
for script in *.init; do
    install -p -D -m755 "$script" "%{buildroot}%{_initrddir}/${script%.init}"
done
cd ..
mkdir -p %{buildroot}/etc/focus
install -p -D -m644 etc/* %{buildroot}/etc/focus

install -d -m755 %{buildroot}%{_localstatedir}/{log,lib,run}/focus
install -p -D -m644 etc/focus.conf %{buildroot}/etc/nginx/conf.d/focus.conf

%clean
%__rm -rf %{buildroot}


%pre
getent group focus >/dev/null || groupadd -r focus
getent passwd focus >/dev/null || \
useradd -r -g focus -d %{_sharedstatedir}/focus -s /sbin/nologin \
-c "Focus Daemon" focus
exit 0


%preun
if [ $1 -eq 0 ] ; then
    /sbin/service focus stop >/dev/null 2>&1
    /sbin/chkconfig --del focus
fi
exit 0


%postun
if [ $1 -eq 1 ] ; then
    /sbin/service focus condrestart
fi
exit 0

%files
%doc README* COPYING
%defattr(-,root,root,-)
%{python_sitelib}/*
%{_usr}/bin/*
%{_initrddir}/*

%attr(775,focus,focus) %dir %{_localstatedir}/*/focus

%defattr(-,focus,focus,-)
%dir /etc/focus
%config(noreplace) /etc/focus/*
%config(noreplace) /etc/nginx/conf.d/focus.conf

%changelog
* Fri May 11 2012 Alessio Ababilov <aababilov@griddynamics.com> - 1.0-0
- Initial RPM release
