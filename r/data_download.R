library(OSTA.data)
library(VisiumIO)
library(SpatialFeatureExperiment)
library(TENxIO)

id <- "VisiumHD_HumanColon_Oliveira"
pa <- OSTA.data_load(id)
dir.create(td <- tempfile())
unzip(pa, exdir=td)

sfe <- TENxVisiumHD(
  segmented_outputs=paste0(td,'/segmented_outputs'),
  processing="filtered",
  format="h5",
  images="lowres",
  sample_id = 'CRC') |>
  import()
