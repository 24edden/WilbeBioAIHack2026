#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p source
curl -fsSL --retry 3 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE28nnn/GSE28460/matrix/GSE28460_series_matrix.txt.gz' -o source/GSE28460_series_matrix.txt.gz
curl -fsSL --retry 3 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE18nnn/GSE18497/matrix/GSE18497_series_matrix.txt.gz' -o source/GSE18497_series_matrix.txt.gz
curl -fsSL --retry 3 'https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/GPL570/annot/GPL570.annot.gz' -o source/GPL570.annot.gz
