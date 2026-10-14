#!/usr/bin/env bash
# Re-download all source data (run from channel/data). Then rebuild the videos.
set -euo pipefail
fred() { curl -sSL "https://fred.stlouisfed.org/graph/fredgraph.csv?id=$1" -o "$2"; }
for id in MORTGAGE30US CSUSHPINSA CUUR0000SEHA MSPUS; do fred $id $id.csv; done
curl -sSL -o histretSP.xls "https://pages.stern.nyu.edu/~adamodar/pc/datasets/histretSP.xls"
curl -sSL -o zhvi_county.csv "https://files.zillowstatic.com/research/public_csvs/zhvi/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
mkdir -p saipe
tail -n +2 ../videos/v02_down_payment/cities.csv | while IFS=, read -r city county st fips; do
  fred "MHI${st}${fips}A052NCEN" "saipe/MHI${st}${fips}A052NCEN.csv"
done
echo done
