#!/bin/ksh
#   script to compute the web monitoring scales
#############################################################################
module load ecmwf-toolbox
module load obstat
module load webdev/feature-eccharts-bologna


mode=$1
inputjsons=${2:-""}
web_package=${3:-"obstat"}
plotdir=$4
margin=${margin:50} ## default = -10


web_package=${web_package:-"obstat"}
if [[ $web_package == "cams_monitoring" ]] ; then
 plotdir=${plotdir:-"/ec/ws3/tc/emos/work/cams/compo/0001/satplots/obstat_cams"}
else
 plotdir=${plotdir:-"/ec/ws3/tc/emos/work/core/pop/oper/0001/satplots/obstat"}
fi


mode_tag="from_${mode_tag}"
[[ $mode == "smosland" ]] && mode_tag="SMOSLAND"
[[ $mode == "smos" ]] && mode_tag="SMOS"
[[ $mode == "gpsro" ]] && mode_tag="gnssro"
[[ $mode == "conv" ]] && mode_tag="conv"
[[ $mode == "surf_conv" ]] && mode_tag="surf_conv"
[[ $mode == @("clrad"|"cllid") ]] && mode_tag="Earthcare"

if [[ $inputjsons == "" ]] ; then
 list_json=$(grep ${mode_tag} *json | cut -f1 -d : | sort | uniq)
else
 list_json=$inputjsons
fi

for inputjson in $(echo $list_json)
do

 outputjson=$(echo $inputjson | cut -f1 -d .)
 outputjson="${outputjson}_new.json"

 update_json_only=""
 if [[ $mode == "satob" && $(grep "hist" $outputjson | wc -l) -gt 0 ]] ; then
  update_json_only="-g"
 fi

 lhist=$(echo $inputjson | grep "hist" || echo "false")
 lhov=$(echo $inputjson | grep "hov" || echo "false")
 lmap=$(echo $inputjson | grep "map" || echo "false")
 lhovlev=$(grep "netcdf_type" $inputjson || echo "false")
 json_type=""
 if [[ $lhist != "false" ]] ; then
  json_type="hist"
 elif [[ $lhovlev != "false" ]] ; then
  json_type="hovlev"
 elif [[ $lhov != "false" ]] ; then
  json_type="hov"
 else
  json_type="geo"
 fi


 list_ncfiles=$(grep "_short" $inputjson | head -1 | cut -f2 -d : | sed 's/[][,"]/ /g' || echo "")
 list_ncfiles=$(grep ${mode_tag} $inputjson | tail -n +2 | cut -f2 -d : | sed 's/[][,"]/ /g' || echo "")

 plots=$plotdir/$mode
 if [[ $mode == "earthcare_lidar" ]] ; then
  plots="$plotdir/windsat"
 elif [[ $mode == "earthcare_radar" ]] ; then
  plots="$plotdir/tmi"
 elif [[ $mode == "mwts3" ]] ; then
  plots="$plotdir/saphir"
 fi

 if [[ $list_ncfiles != "" ]] ; then
  list_available_ncfile=""
  set -vx
  for ncfile in $(echo $list_ncfiles)
  do
   if [[ -f $plots/$ncfile.nc ]] ; then
    list_available_ncfile="$list_available_ncfile $plots/$ncfile.nc"
   fi
  done
  echo ${list_ncfiles} $plots
  python3 ${OBSTAT_HOME}/scripts/create_web_scaling.py -i "${list_available_ncfile}" -j $inputjson -o $outputjson -m $json_type -t $margin ${update_json_only}
  web-catalogue -s bol-prod -a push -p ${web_package} $outputjson
  rm -f $outputjson
 fi
done
