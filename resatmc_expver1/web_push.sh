module load webdev

#Push to TEST
#https://charts-test.ecmwf.int/catalogue/packages/cams_monitoring
web-catalogue -s bol-test -a push -p cams_monitoring *json

#Push to PRODUCTION
#https://atmosphere.copernicus.eu/charts/packages/cams_monitoring
#commented out:
#web-catalogue -s bol-prod -a push -p cams_monitoring *json
