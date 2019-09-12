# Run tests (requires network connectivity)
%global with_check 0

# Prebuilt binaries break build process for CentOS. Disable debug packages to resolve
%if 0%{?rhel}
%define debug_package %{nil}
%endif

%global provider        github
%global provider_tld    com
%global project         prometheus
%global repo            alertmanager
# https://github.com/prometheus/alertmanager/
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}

Name:           golang-%{provider}-%{project}-%{repo}
Version:        0.19.0
Release:        3%{?dist}
Summary:        Prometheus Alertmanager
License:        ASL 2.0
URL:            https://%{provider_prefix}
Source0:        https://%{provider_prefix}/archive/v%{version}.tar.gz
Source1:        alertmanager.service

Provides:       alertmanager = %{version}-%{release}

%if 0%{?rhel} != 6
BuildRequires:  systemd
%endif

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 aarch64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}

%description
The Alertmanager handles alerts sent by client applications such as the Prometheus server.
It takes care of deduplicating, grouping, and routing them to the correct receiver integrations such as email, PagerDuty, or OpsGenie.
It also takes care of silencing and inhibition of alerts.


%prep
%setup -q -n %{repo}-%{version}

%build
export GO111MODULE=on
cd cmd/alertmanager
go build -ldflags=-linkmode=external -mod vendor -o alertmanager
cd ../amtool
go build -ldflags=-linkmode=external -mod vendor -o amtool

%install
%if 0%{?rhel} != 6
install -d -p   %{buildroot}%{_unitdir}
%endif

install -Dpm 0644 doc/examples/simple.yml %{buildroot}%{_sysconfdir}/alertmanager/alertmanager.yml
install -Dpm 0755 cmd/alertmanager/alertmanager %{buildroot}%{_sbindir}/alertmanager
install -Dpm 0755 cmd/amtool/amtool %{buildroot}%{_bindir}/amtool
%if 0%{?rhel} != 6
install -Dpm 0644 %{SOURCE1} %{buildroot}%{_unitdir}/alertmanager.service
%endif
install -dm 0750 %{buildroot}%{_sharedstatedir}/alertmanager/

%if 0%{?with_check}
%check
export GO111MODULE=on
cd cmd/alertmanager
go test -mod vendor
cd ../amtool
go test -mod vendor
%endif


%files
%if 0%{?rhel} != 6
%{_unitdir}/alertmanager.service
%endif
%attr(0640, prometheus, prometheus) %config(noreplace) %{_sysconfdir}/alertmanager/alertmanager.yml
%license LICENSE
%doc README.md CHANGELOG.md doc/
%attr(0750, alertmanager, alertmanager) %dir %{_sharedstatedir}/alertmanager/
%{_sbindir}/alertmanager
%{_bindir}/amtool

%pre
getent group alertmanager > /dev/null || groupadd -r alertmanager
getent passwd alertmanager > /dev/null || \
    useradd -Mrg alertmanager -s /sbin/nologin \
            -c "Alertmanager - Prometheus alerting system" alertmanager

%post
%if 0%{?rhel} != 6
%systemd_post alertmanager.service
%endif

%preun
%if 0%{?rhel} != 6
%systemd_preun alertmanager.service
%endif

%postun
%if 0%{?rhel} != 6
%systemd_postun alertmanager.service
%endif

%changelog
* Thu Sep 12 2019 Ben Reedy <breed808@breed808.com> - 0.19.0-3
- Disable creation of home directory for alertmanager user
