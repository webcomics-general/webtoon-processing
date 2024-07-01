"""Run webtoon postprocessor from the command line.

This file is executed when the package is run as a script, that is to
say when it is run on the command line with the `-m` option [1], for
instance:

```shell
python3 -m webtoon_processing --help
```

[1] https://docs.python.org/3/library/__main__.html
"""

from webtoon_processing.webtoon_processing import main

main()
