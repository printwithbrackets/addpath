pkgname=addpath-git
pkgver=1.0.0.r0.g0000000
pkgrel=1
pkgdesc="TUI PATH manager — scan, add, and remove PATH entries interactively"
arch=('any')
url="https://github.com/yourusername/addpath"
license=('MIT')
depends=('python' 'python-textual')
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
    install -Dm644 addpath.1  "$pkgdir/usr/share/man/man1/addpath.1"
    install -Dm644 LICENSE    "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
