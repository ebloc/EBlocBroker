#!bin/bash 

#sudo killall cat
while [ 1 ]
do
    cat /eBloc/fifo | xargs -I {} bash orcid.sh {}
done




