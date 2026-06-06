# Maintainer: JoeJoeTV <joejoetv@joejoetv.de>

pkgname=nemo-kdeconnect
pkgver=1.0.2
pkgrel=1
pkgdesc='Extension for the Nemo file manager that adds the ability to send files to devices connected using KDEConnect directly from Nemo.'
arch=('all')
url="https://github.com/JoeJoeTV/nemo-extension-kdeconnect"
license=('GPL-3')
depends=('python3' 'nemo' 'kdeconnect' 'python-nemo')
provides=('nemo-kdeconnect')
#sha256sums=('SKIP')

build() {
    # Compile localization files to .mo
    find "${srcdir}/nemo-kdeconnect/locale/" -name \*.po -print -execdir sh -c 'msgfmt -f -o "$(basename "$0" .po).mo" "$0"' '{}' \;
}

package() {
    install -D "${srcdir}/nemo-kdeconnect.py" "${pkgdir}/usr/share/nemo-python/extensions/nemo-kdeconnect.py"
    cd nemo-kdeconnect
    find "locale/" -type f -name \*.mo -print -exec install -D "${srcdir}/nemo-kdeconnect/{}" "${pkgdir}/usr/share/{}" \;
    cd ..
}
