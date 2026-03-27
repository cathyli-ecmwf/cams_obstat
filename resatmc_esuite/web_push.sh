module load webdev

#Push to TEST
#https://charts-test.ecmwf.int/catalogue/packages/cams_monitoring_esuite
web-catalogue -s bol-test -a list all -p cams_monitoring_esuite > cams_monitoring_esuite.bol-test.list
for p in $(cat cams_monitoring_esuite.bol-test.list); do web-catalogue -s bol-test -a remove $p -p cams_monitoring_esuite; done
web-catalogue -s bol-test -a push -p cams_monitoring_esuite *json

#Push to PRODUCTION
#https://atmosphere.copernicus.eu/charts/packages/cams_monitoring_esuite
#commented out:
#web-catalogue -s bol-prod -a push -p cams_monitoring_esuite *json
