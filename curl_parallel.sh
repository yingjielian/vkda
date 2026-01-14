#!/bin/bash
PARALLELISM=$1
CURRENT_TS=$(date +%s | sed "s/ //g")
CURL_URL=$2

for i in $(seq -w 1 $PARALLELISM); do
    rm ./curl.${i}.output.txt 2> /dev/null
    rm ./curl.${i}.header.txt 2> /dev/null
    DELTA=$((10 * $(echo $i | sed 's/^0\+//g') ))
    END_TS=$((${CURRENT_TS} - ${DELTA}))
    FINAL_URL="${CURL_URL}?endTimestamp=${END_TS}"
    echo $i $FINAL_URL
    curl -v -D ./curl.${i}.header.txt ${FINAL_URL} > ./curl.${i}.output.txt 2> /dev/null &
done

rm ./curl_output.txt 2> /dev/null

for i in $(seq -w 1 $PARALLELISM); do
    while [[ ! -s ./curl.${i}.output.txt ]]; do
	echo "Waiting for request $i"
	sleep 1
    done
    echo "Request $i:" >> curl_output.txt
    head -n 1 ./curl.${i}.header.txt >> ./curl_output.txt
    cat ./curl.${i}.output.txt >> ./curl_output.txt
    echo "" >> ./curl_output.txt
done

cat ./curl_output.txt




