# Changelog

## [0.5.1](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/compare/v0.5.0...v0.5.1) (2025-04-08)


### Bug Fixes

* Add log retrieval after job finalization ([#61](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/61)) ([c273f29](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/c273f292963b6eb6db528f139df201eca4fd282e))
* batch job ID and label prior to submission ([#59](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/59)) ([3a37591](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/3a3759109d98f344caebd93ddfa6ff8ac39e3437))

## [0.5.0](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/compare/v0.4.0...v0.5.0) (2024-08-14)


### Features

* Add support for customer compute service account ([#51](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/51), [@hnawar](https://github.com/hnawar)) ([#52](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/52)) ([8678e20](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/8678e20db8979c07089a7a9f9dd108a912d5107f))

## [0.4.0](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/compare/v0.3.3...v0.4.0) (2024-05-07)


### Features

* add support for using the COS version of google batch ([b0b7614](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/b0b7614e37a05f45cce2861b53fa417bbfed59b8))
* landsat example ([#50](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/50)) ([944767f](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/944767f7d80b56f37e3982d9dace6d97de46f718))

## [0.3.3](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/compare/v0.3.2...v0.3.3) (2024-04-06)


### Bug Fixes

* make get_snakefile return rel path to snakefile ([#40](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/40)) ([#41](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/41)) ([de2b1da](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/de2b1da1e303a21824408ceea0e316c42e4d1a86))

## [0.3.2](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/compare/v0.3.1...v0.3.2) (2024-04-05)


### Bug Fixes

* ensure we install datrie ([#37](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/37)) ([62f7404](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/62f740452ad2a607762040e5e315360f7917a6c6))

## [0.3.1](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/compare/v0.3.0...v0.3.1) (2024-03-12)


### Bug Fixes

* update to latest interface ([#30](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/30)) ([af536dc](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/af536dc744fddccd6da5221bef1539c4d6fc173d))

## [0.3.0](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/compare/v0.2.0...v0.3.0) (2024-02-15)


### Features

* add simple example with cos ([#22](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/22)) ([2951454](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/2951454defef65a24396a16f7b9c4103e4156571))
* add support for Google Batch GPUs ([#26](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/26)) ([f2af21c](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/f2af21c6804d5c687d2bc9443497c98fb60641bc))
* expose network policy interfaces ([#28](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/28)) ([41c8d44](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/41c8d447502d5bba485b14ebe1eab1f2bf6b50dd))
* preemption ([#25](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/25)) ([d6913a1](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/d6913a13b59f94b4f7c590dfe8c446c535f5c883))
* support for boot disk type, size, and image ([#27](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/27)) ([d5de5a1](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/d5de5a136a63686e8c41077a6cd4aa96816f4a93))

## [0.2.0](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/compare/v0.1.1...v0.2.0) (2024-01-02)


### Features

* add/intel mpi example ([#20](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/20)) ([673ad34](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/673ad345fb6590696dc3bb3d88c6873abde068ef))

## [0.1.1](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/compare/v0.1.0...v0.1.1) (2023-12-20)


### Bug Fixes

* remove superfluous container image settings ([0390deb](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/0390deb3a1995587dab611629ffedac716b87566))

## 0.1.0 (2023-12-08)


### Features

* add/googlebatch logging testing ([#13](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/13)) ([a3efcaa](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/a3efcaa991769f905e2c9bb8195481528d10d3c8))
* upload to google storage build cache and download script ([6c8cdbd](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/6c8cdbd7e84e244aeff199bbf8542d2f2633fe38))


### Bug Fixes

* adapt to interface changes; cleanup unnecessary code (source code upload and deployment is now handled by Snakemake itself) ([#9](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/9)) ([c364e7f](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/c364e7f97f78233dab6bedb4469e1c94d4e7cdcc))


### Documentation

* update metadata ([3374341](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/commit/33743410cf8ca84ba8d3dc166c0ad3afdc769959))
