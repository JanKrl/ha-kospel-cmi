# Changelog

## [3.0.0](https://github.com/JanKrl/ha-kospel-cmi/compare/lib-v2.0.0...lib-v3.0.0) (2026-08-01)


### ⚠ BREAKING CHANGES

* **lib:** Renamed CWU/CO properties and enums to use DHW/CH prefixes across the library API.

### Features

* **lib:** add daily schedules handling ([#115](https://github.com/JanKrl/ha-kospel-cmi/issues/115)) ([dd0b497](https://github.com/JanKrl/ha-kospel-cmi/commit/dd0b497427d1e483d8aaddb170a7b9b2ac42a521))
* **lib:** trigger major release for lib ([#123](https://github.com/JanKrl/ha-kospel-cmi/issues/123)) ([a1f676c](https://github.com/JanKrl/ha-kospel-cmi/commit/a1f676cdebe271fecad76438050c4ede261d05d3))


### Bug Fixes

* correct valve position mapping ([#100](https://github.com/JanKrl/ha-kospel-cmi/issues/100)) ([4ca4922](https://github.com/JanKrl/ha-kospel-cmi/commit/4ca49229f80dcbc85bfa9f52fd95025b172572b7))
* **ha:** remove aiohttp strict constraint to fix HA core conflict ([48565c7](https://github.com/JanKrl/ha-kospel-cmi/commit/48565c70501f4858fb96be5028b0376da41f998f))
* **ha:** remove strict aiohttp requirement ([#80](https://github.com/JanKrl/ha-kospel-cmi/issues/80)) ([223f763](https://github.com/JanKrl/ha-kospel-cmi/commit/223f7637e1237ef7c2967672f1e22efe16580423))
* relax library dependency versions for HA compatibility ([#90](https://github.com/JanKrl/ha-kospel-cmi/issues/90)) ([13cd1e6](https://github.com/JanKrl/ha-kospel-cmi/commit/13cd1e6a8e2c66f5bea86af1fc370f1f31f8ff16))
* rename cwu/co identifiers to dhw/ch across codebase ([033d382](https://github.com/JanKrl/ha-kospel-cmi/commit/033d382c8e46a52332ca9733b8523be4987f2682))
* resolve enum error by publishing library and forcing upgrade ([#87](https://github.com/JanKrl/ha-kospel-cmi/issues/87)) ([8c79abf](https://github.com/JanKrl/ha-kospel-cmi/commit/8c79abf46962dccbfbc79252d9d615acd95a8cde))
* standardize enum values and resolve translation mismatches ([#66](https://github.com/JanKrl/ha-kospel-cmi/issues/66)) ([f05e68b](https://github.com/JanKrl/ha-kospel-cmi/commit/f05e68b8176687f8174fe622bd87320c09eaccd7))


### Documentation

* document schedule register mapping ([#109](https://github.com/JanKrl/ha-kospel-cmi/issues/109)) ([aa1dbfe](https://github.com/JanKrl/ha-kospel-cmi/commit/aa1dbfe580db40408b683d92f87b9fed6ab2e106))

## [2.0.0](https://github.com/JanKrl/ha-kospel-cmi/compare/lib-v1.1.6...lib-v2.0.0) (2026-08-01)


### ⚠ BREAKING CHANGES

* **lib:** Renamed CWU/CO properties and enums to use DHW/CH prefixes across the library API.

### Features

* **lib:** add daily schedules handling ([#115](https://github.com/JanKrl/ha-kospel-cmi/issues/115)) ([dd0b497](https://github.com/JanKrl/ha-kospel-cmi/commit/dd0b497427d1e483d8aaddb170a7b9b2ac42a521))
* **lib:** trigger major release for lib ([#123](https://github.com/JanKrl/ha-kospel-cmi/issues/123)) ([a1f676c](https://github.com/JanKrl/ha-kospel-cmi/commit/a1f676cdebe271fecad76438050c4ede261d05d3))


### Bug Fixes

* rename cwu/co identifiers to dhw/ch across codebase ([033d382](https://github.com/JanKrl/ha-kospel-cmi/commit/033d382c8e46a52332ca9733b8523be4987f2682))


### Documentation

* document schedule register mapping ([#109](https://github.com/JanKrl/ha-kospel-cmi/issues/109)) ([aa1dbfe](https://github.com/JanKrl/ha-kospel-cmi/commit/aa1dbfe580db40408b683d92f87b9fed6ab2e106))
