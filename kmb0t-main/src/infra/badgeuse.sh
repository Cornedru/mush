
#
# This script goes to rpi where student can scan their RFID card.
# Refer to https://gitlab.42mulhouse.fr/Yohan/badgeuse for installation
#

BOT_URL='https://webhook.42mulhouse.fr/h/campus'

while true
do
  read badge

  json_payload=$(cat <<EOF
{
  "type": "badgeuse",
  "where": "$(hostname)",
  "when": "$(date +'%d/%m/%Y %H:%M')",
  "badge": "$badge",
  "details": "SECURED",
  "hash": ""
}
EOF
)

  curl --verbose -X POST -d "$json_payload" -H "Content-Type: application/json" "$BOT_URL"

done