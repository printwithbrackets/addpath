pkgname=addpath-git
pkgver=1.0.0.r0.g0000000
pkgrel=1
pkgdesc="hunt down executables not in your PATH and fix it"
arch=('any')
url="https://github.com/yourusername/addpath"
license=('MIT')
depends=('python')
makedepends=('git')
provides=('addpath')
conflicts=('addpath')

source=("git+https://github.com/yourusername/addpath.git")
sha256sums=('SKIP')

pkgver() {
    cd "$srcdir/addpath"
    git describe --long --tags --always | sed 's/^v//;s/-/./g'
}

package() {
    cd "$srcdir/addpath"
    install -Dm755 addpath.py "$pkgdir/usr/bin/addpath"
}
