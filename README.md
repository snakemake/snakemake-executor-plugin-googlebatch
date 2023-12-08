# Snakemake executor plugin: google-batch

This is the [Google Batch](https://cloud.google.com/batch/docs/get-started) external executor plugin for snakemake.
For documentation, see the [Snakemake plugin catalog](https://snakemake.github.io/snakemake-plugin-catalog/plugins/executor/googlebatch.html).

###  TODO

- Add bash strict mode (should default to true)
- Integrate snakemake MPI support (needs to work with snippet)


### Questions

- What leads to STATE_UNSPECIFIED?
- For Google: what is the source of truth (listing) for batch? I see different answers in different places.
- For Johannes: Why can't we use debug logging for executor plugins? I instead need to use info and make it very verbose.
- For All: How do we want to use [COS](https://cloud.google.com/container-optimized-os/docs/concepts/features-and-benefits)? It would allow a container base to be used instead I think?

### Notes

- Conda is used to install Snakemake and dependencies.
- The COS (container OS) uses the default Snakemake container, unless you specify differently.

### Feedback

- Debugging batch is impossible (and slow). A "hello world" workflow takes 10 minutes to run and debug once.
- The jobs table is slow to load and sometimes does not load / shows old jobs at the top (without me touching anything)
- The logs directly in batch are so much better! Having the stream option there would still be nice (vs. having to refresh.)
- The batch UI (jobs table) is very slow to load and often just doesn't even after button or page refresh.

For examples, look into the [examples](examples) directory.


## Developer

The instructions for creating and scaffolding this plugin are [here](https://github.com/snakemake/poetry-snakemake-plugin#scaffolding-an-executor-plugin).
Instructions for writing your plugin with examples are provided via the [snakemake-executor-plugin-interface](https://github.com/snakemake/snakemake-executor-plugin-interface).


## License

HPCIC DevTools is distributed under the terms of the MIT license.
All new contributions must be made under this license.

See [LICENSE](https://github.com/converged-computing/cloud-select/blob/main/LICENSE),
[COPYRIGHT](https://github.com/converged-computing/cloud-select/blob/main/COPYRIGHT), and
[NOTICE](https://github.com/converged-computing/cloud-select/blob/main/NOTICE) for details.

SPDX-License-Identifier: (MIT)

LLNL-CODE- 842614