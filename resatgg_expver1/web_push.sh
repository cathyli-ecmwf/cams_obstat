module load webdev

#Push to TEST
#https://charts-test.ecmwf.int/catalogue/packages/cams_ghg_monitoring
web-catalogue -s bol-test -a list all -p cams_ghg_monitoring > cams_ghg_monitoring.bol-test.list
for p in $(cat cams_ghg_monitoring.bol-test.list); do web-catalogue -s bol-test -a remove $p -p cams_ghg_monitoring ; done
web-catalogue -s bol-test -a push -p cams_ghg_monitoring *json

#Push to PRODUCTION
#https://atmosphere.copernicus.eu/charts/packages/cams_ghg_monitoring
#commented out:
#web-catalogue -s bol-prod -a list all -p cams_ghg_monitoring > cams_ghg_monitoring.bol-prod.list
#for p in $(cat cams_ghg_monitoring.bol-prod.list); do web-catalogue -s bol-prod -a remove $p -p cams_ghg_monitoring ; done
#web-catalogue -s bol-prod -a push -p cams_ghg_monitoring *json
